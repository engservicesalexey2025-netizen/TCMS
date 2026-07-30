import uuid
from datetime import date, timedelta
from io import BytesIO
from typing import Annotated

import openpyxl
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, or_, select

from app.api.deps import DbSession, require_permission
from app.api.v1.crud_router import build_crud_router
from app.models.audit import AuditLog
from app.models.contractor import Contractor
from app.models.enums import AuditAction, ProjectStatus
from app.models.org import City, OrgUnit
from app.models.project import (
    ConstructionObject,
    ControlSystem,
    Contour,
    Project,
    ProjectStage,
    ProjectType,
)
from app.models.project_document import ProjectDocument
from app.models.user import User
from app.schemas.common import Page
from app.schemas.project import (
    ConstructionObjectCreate,
    ConstructionObjectOut,
    ConstructionObjectUpdate,
    ContourCreate,
    ContourOut,
    ControlSystemCreate,
    ControlSystemOut,
    ProjectCreate,
    ProjectHistoryEntryOut,
    ProjectOut,
    ProjectStageCreate,
    ProjectStageOut,
    ProjectTypeCreate,
    ProjectTypeOut,
    ProjectUpdate,
)
from app.services.audit import log_action
from app.services.crud_base import AuditedRepository
from app.services.data_scope import apply_data_scope

projects_router = APIRouter(prefix="/projects", tags=["projects"])
router = projects_router

repo = AuditedRepository(Project, search_fields=["Name", "Address", "ContractNumber"])

ViewUser = Annotated[User, Depends(require_permission("PROJECTS", "VIEW"))]
CreateUser = Annotated[User, Depends(require_permission("PROJECTS", "CREATE"))]
UpdateUser = Annotated[User, Depends(require_permission("PROJECTS", "UPDATE"))]
DeleteUser = Annotated[User, Depends(require_permission("PROJECTS", "DELETE"))]
ExportUser = Annotated[User, Depends(require_permission("PROJECTS", "EXPORT"))]

project_types_router = build_crud_router(
    model=ProjectType,
    create_schema=ProjectTypeCreate,
    update_schema=ProjectTypeCreate,
    out_schema=ProjectTypeOut,
    prefix="/project-types",
    tags=["project-types"],
    search_fields=["Name"],
    module="PROJECT_TYPES",
)

project_stages_router = build_crud_router(
    model=ProjectStage,
    create_schema=ProjectStageCreate,
    update_schema=ProjectStageCreate,
    out_schema=ProjectStageOut,
    prefix="/project-stages",
    tags=["project-stages"],
    search_fields=["Name"],
    module="PROJECT_STAGES",
)

contours_router = build_crud_router(
    model=Contour,
    create_schema=ContourCreate,
    update_schema=ContourCreate,
    out_schema=ContourOut,
    prefix="/contours",
    tags=["contours"],
    search_fields=["Name"],
    module="CONTOURS",
)

control_systems_router = build_crud_router(
    model=ControlSystem,
    create_schema=ControlSystemCreate,
    update_schema=ControlSystemCreate,
    out_schema=ControlSystemOut,
    prefix="/control-systems",
    tags=["control-systems"],
    search_fields=["Name"],
    module="CONTROL_SYSTEMS",
)

objects_router = build_crud_router(
    model=ConstructionObject,
    create_schema=ConstructionObjectCreate,
    update_schema=ConstructionObjectUpdate,
    out_schema=ConstructionObjectOut,
    prefix="/objects",
    tags=["objects"],
    search_fields=["Name", "Address"],
    module="OBJECTS",
)

# Прямые текстовые колонки Project, участвующие в префиксном поиске.
_PROJECT_TEXT_FIELDS = ["Name", "Address", "ContractNumber", "GaskTicketNumber", "GaskNotificationNumber"]


def build_project_search_query(db: DbSession, user: User, search: str | None, include_archived: bool):
    """Аналогично build_employee_search_query — префиксный поиск по всем
    текстовым колонкам Project плюс подписанные значения справочников
    (Город, Управление, Тип/Стадия/Контур/Система, все 4 роли подрядчиков).
    Применяет Row-Level Security по организации (§15 ТЗ).
    """
    developer = Contractor.__table__.alias("developer")
    contractor = Contractor.__table__.alias("contractor")
    general_contractor = Contractor.__table__.alias("general_contractor")
    subcontractor = Contractor.__table__.alias("subcontractor")

    query = (
        select(Project)
        .outerjoin(City, City.Id == Project.CityId)
        .outerjoin(OrgUnit, OrgUnit.Id == Project.OrgUnitId)
        .outerjoin(ProjectType, ProjectType.Id == Project.ProjectTypeId)
        .outerjoin(ProjectStage, ProjectStage.Id == Project.ProjectStageId)
        .outerjoin(Contour, Contour.Id == Project.ContourId)
        .outerjoin(ControlSystem, ControlSystem.Id == Project.ControlSystemId)
        .outerjoin(developer, developer.c.Id == Project.DeveloperId)
        .outerjoin(contractor, contractor.c.Id == Project.ContractorId)
        .outerjoin(general_contractor, general_contractor.c.Id == Project.GeneralContractorId)
        .outerjoin(subcontractor, subcontractor.c.Id == Project.SubcontractorId)
    )
    if not include_archived:
        query = query.where(Project.IsActive.is_(True))
    if search:
        pattern = f"{search}%"
        conditions = [getattr(Project, f).ilike(pattern) for f in _PROJECT_TEXT_FIELDS]
        conditions += [
            City.Name.ilike(pattern),
            OrgUnit.Name.ilike(pattern),
            ProjectType.Name.ilike(pattern),
            ProjectStage.Name.ilike(pattern),
            Contour.Name.ilike(pattern),
            ControlSystem.Name.ilike(pattern),
            developer.c.Name.ilike(pattern),
            contractor.c.Name.ilike(pattern),
            general_contractor.c.Name.ilike(pattern),
            subcontractor.c.Name.ilike(pattern),
        ]
        query = query.where(or_(*conditions))
    return apply_data_scope(query, Project, user, db)


def _check_project_data_scope_or_404(db: DbSession, user: User, project: Project) -> None:
    from app.services.access import get_accessible_org_unit_ids

    accessible = get_accessible_org_unit_ids(db, user)
    if accessible is None:
        return
    if project.OrgUnitId is None or project.OrgUnitId not in accessible:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")


# Query param value -> column checked for emptiness by the "quick filter"
# chips on the frontend (missing-data at-a-glance panel).
_PROJECT_MISSING_FIELD_COLUMNS = {
    "city": Project.CityId,
    "org_unit": Project.OrgUnitId,
    "project_type": Project.ProjectTypeId,
    "project_stage": Project.ProjectStageId,
    "control_system": Project.ControlSystemId,
    "contract_number": Project.ContractNumber,
    "area": Project.Area,
    "cost": Project.Cost,
    "gis_link": Project.GisLink,
    "gask_notification_number": Project.GaskNotificationNumber,
}


def _add_one_month(value: date) -> date:
    if value.month == 12:
        return value.replace(year=value.year + 1, month=1)
    try:
        return value.replace(month=value.month + 1)
    except ValueError:
        # e.g. 31 января -> февраль не имеет 31 числа, берём последний день месяца.
        next_month = value.month + 1
        following = value.replace(month=next_month, day=1) + timedelta(days=32)
        return following.replace(day=1) - timedelta(days=1)


@router.get("", response_model=Page[ProjectOut])
def list_projects(
    db: DbSession,
    user: ViewUser,
    skip: int = 0,
    limit: int = 50,
    search: str | None = None,
    include_archived: bool = False,
    missing_field: str | None = None,
):
    query = build_project_search_query(db, user, search, include_archived)
    column = _PROJECT_MISSING_FIELD_COLUMNS.get(missing_field) if missing_field else None
    if column is not None:
        query = query.where(column.is_(None))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.offset(skip).limit(limit)).all()
    return Page(items=items, total=total, skip=skip, limit=limit)


_STATUS_LABELS = {
    ProjectStatus.PLANNED: "Планируется",
    ProjectStatus.IN_PROGRESS: "Активный",
    ProjectStatus.COMPLETED: "Завершён",
    ProjectStatus.SUSPENDED: "Приостановлен",
}


@router.get("/export")
def export_projects(
    db: DbSession,
    user: ExportUser,
    search: str | None = None,
    include_archived: bool = False,
):
    """Экспорт в Excel — уважает текущий фильтр (search/include_archived),
    как список; все столбцы карточки плюс список приложенных файлов,
    свёрнутый в одну колонку через "; " (аналогично /employees/export)."""
    query = build_project_search_query(db, user, search, include_archived)
    projects = db.scalars(query).all()

    cities = {c.Id: c.Name for c in db.scalars(select(City)).all()}
    org_units = {o.Id: o.Name for o in db.scalars(select(OrgUnit)).all()}
    project_types = {t.Id: t.Name for t in db.scalars(select(ProjectType)).all()}
    project_stages = {s.Id: s.Name for s in db.scalars(select(ProjectStage)).all()}
    contours = {c.Id: c.Name for c in db.scalars(select(Contour)).all()}
    control_systems = {s.Id: s.Name for s in db.scalars(select(ControlSystem)).all()}
    contractors = {c.Id: c.Name for c in db.scalars(select(Contractor)).all()}

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Проекты"
    sheet.append([
        "Наименование", "Город", "Адрес", "Описание", "Управление",
        "Тип проекта", "Стадия проекта", "Контур", "Система контроля", "Статус",
        "Застройщик", "Подрядчик", "Ген подрядчик", "Суб подрядчик",
        "№ договора", "Площадь объекта", "Стоимость договора", "2GIS (ссылка)",
        "Номер талона ГАСК", "Номер уведомления ГАСК", "Дата талона ГАСК",
        "Срок действия талона ГАСК", "Фактическая дата окончания",
        "Файлы",
    ])

    for project in projects:
        documents = db.scalars(
            select(ProjectDocument).where(
                ProjectDocument.ProjectId == project.Id,
                ProjectDocument.IsActive.is_(True),
            )
        ).all()
        file_names = "; ".join(d.FileName for d in documents)
        sheet.append([
            project.Name,
            cities.get(project.CityId, ""),
            project.Address or "",
            project.Description or "",
            org_units.get(project.OrgUnitId, ""),
            project_types.get(project.ProjectTypeId, ""),
            project_stages.get(project.ProjectStageId, ""),
            contours.get(project.ContourId, ""),
            control_systems.get(project.ControlSystemId, ""),
            _STATUS_LABELS.get(project.Status, project.Status),
            contractors.get(project.DeveloperId, ""),
            contractors.get(project.ContractorId, ""),
            contractors.get(project.GeneralContractorId, ""),
            contractors.get(project.SubcontractorId, ""),
            project.ContractNumber or "",
            float(project.Area) if project.Area is not None else "",
            float(project.Cost) if project.Cost is not None else "",
            project.GisLink or "",
            project.GaskTicketNumber or "",
            project.GaskNotificationNumber or "",
            project.GaskTicketDate.isoformat() if project.GaskTicketDate else "",
            project.GaskTicketExpiryDate.isoformat() if project.GaskTicketExpiryDate else "",
            project.ActualEndDate.isoformat() if project.ActualEndDate else "",
            file_names,
        ])

    log_action(
        db, table_name="Projects", record_id=uuid.uuid4(), action=AuditAction.EXPORT,
        user_id=user.Id, reason=f"Экспорт списка проектов (search={search!r})",
    )
    db.commit()

    buffer = BytesIO()
    workbook.save(buffer)
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=projects_export.xlsx"},
    )


@router.get("/stats")
def project_stats(db: DbSession, user: ViewUser, include_archived: bool = False):
    """Счётчики для панели быстрых фильтров плюс контроль сроков действия
    талона ГАСК: сколько проектов истекают в течение месяца (жёлтые строки)
    и сколько уже просрочены (красные строки) — используется баннерами
    уведомлений наверху страницы."""
    base_query = apply_data_scope(select(Project), Project, user, db)
    if not include_archived:
        base_query = base_query.where(Project.IsActive.is_(True))
    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0

    counts = {"Total": total}
    for key, column in _PROJECT_MISSING_FIELD_COLUMNS.items():
        missing_query = base_query.where(column.is_(None))
        counts[key] = db.scalar(select(func.count()).select_from(missing_query.subquery())) or 0

    today = date.today()
    horizon = _add_one_month(today)
    expiring_query = base_query.where(
        Project.GaskTicketExpiryDate.is_not(None),
        Project.GaskTicketExpiryDate >= today,
        Project.GaskTicketExpiryDate <= horizon,
    )
    expired_query = base_query.where(
        Project.GaskTicketExpiryDate.is_not(None),
        Project.GaskTicketExpiryDate < today,
    )
    counts["GaskExpiringSoon"] = db.scalar(
        select(func.count()).select_from(expiring_query.subquery())
    ) or 0
    counts["GaskExpired"] = db.scalar(
        select(func.count()).select_from(expired_query.subquery())
    ) or 0
    return counts


@router.get("/{item_id}", response_model=ProjectOut)
def get_project(item_id: uuid.UUID, db: DbSession, user: ViewUser):
    obj = repo.get(db, item_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
    _check_project_data_scope_or_404(db, user, obj)
    return obj


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(data: ProjectCreate, db: DbSession, user: CreateUser):
    return repo.create(db, data.model_dump(), user.Id)


@router.patch("/{item_id}", response_model=ProjectOut)
def update_project(item_id: uuid.UUID, data: ProjectUpdate, db: DbSession, user: UpdateUser):
    existing = repo.get(db, item_id)
    if existing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
    _check_project_data_scope_or_404(db, user, existing)
    obj = repo.update(db, item_id, data.model_dump(exclude_unset=True), user.Id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
    return obj


@router.post("/{item_id}/archive", response_model=ProjectOut)
def archive_project(item_id: uuid.UUID, db: DbSession, user: DeleteUser):
    existing = repo.get(db, item_id)
    if existing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
    _check_project_data_scope_or_404(db, user, existing)
    obj = repo.archive(db, item_id, user.Id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
    return obj


@router.post("/{item_id}/restore", response_model=ProjectOut)
def restore_project(item_id: uuid.UUID, db: DbSession, user: DeleteUser):
    existing = repo.get(db, item_id)
    if existing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
    _check_project_data_scope_or_404(db, user, existing)
    obj = repo.restore(db, item_id, user.Id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
    return obj


@router.get("/{item_id}/history", response_model=Page[ProjectHistoryEntryOut])
def project_history(
    item_id: uuid.UUID,
    db: DbSession,
    user: ViewUser,
    skip: int = 0,
    limit: int = 50,
):
    existing = repo.get(db, item_id)
    if existing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
    _check_project_data_scope_or_404(db, user, existing)

    query = (
        select(AuditLog, User.Login)
        .join(User, User.Id == AuditLog.ChangedByUserId, isouter=True)
        .where(AuditLog.TableName == "Projects", AuditLog.RecordId == item_id)
        .order_by(AuditLog.ChangedDate.desc())
    )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(query.offset(skip).limit(limit)).all()

    entries = [
        ProjectHistoryEntryOut(
            Id=log.Id,
            Action=log.Action,
            ChangedByUserId=log.ChangedByUserId,
            ChangedByLogin=login,
            ChangedDate=log.ChangedDate,
            FieldName=log.FieldName,
            OldValue=log.OldValue,
            NewValue=log.NewValue,
        )
        for log, login in rows
    ]
    return Page(items=entries, total=total, skip=skip, limit=limit)
