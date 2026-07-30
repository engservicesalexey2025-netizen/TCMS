import uuid
from io import BytesIO
from typing import Annotated

import openpyxl
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, or_, select

from app.api.deps import DbSession, require_permission
from app.models.audit import AuditLog
from app.models.employee import Employee
from app.models.employee_certificate import CertificationLevel, EmployeeCertificate
from app.models.enums import AuditAction, EmployeeStatus, Gender
from app.models.org import City, LegalEntity, Position
from app.models.user import User
from app.schemas.common import Page
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeHistoryEntryOut,
    EmployeeOut,
    EmployeeUpdate,
)
from app.services.audit import log_action
from app.services.crud_base import AuditedRepository
from app.services.data_scope import apply_data_scope
from app.services.field_security import apply as apply_field_security, get_field_modes
from app.services.masking import compute_tenure, mask_iin

router = APIRouter(prefix="/employees", tags=["employees"])

repo = AuditedRepository(Employee, search_fields=["FullName", "Email", "IIN"])

# Text columns living directly on Employees, searched by prefix ("по начальным
# буквам") — covers everything the generic AuditedRepository.list() can reach
# without a join.
_EMPLOYEE_TEXT_FIELDS = ["FullName", "Email", "IIN", "CorporatePhone", "PersonalPhone"]


def build_employee_search_query(db: DbSession, user: User, search: str | None, include_archived: bool):
    """Shared by list_employees and the Excel export: prefix-matches `search`
    across every employee-facing column shown in the table, including the
    resolved reference labels (Position/City/LegalEntity), which requires a
    join — the generic AuditedRepository.list() only searches raw columns on
    the entity's own table, so this bypasses it for Employees specifically.
    Also applies Row-Level Security by organization (§15 ТЗ).
    """
    query = (
        select(Employee)
        .outerjoin(Position, Position.Id == Employee.PositionId)
        .outerjoin(City, City.Id == Employee.CityId)
        .outerjoin(LegalEntity, LegalEntity.Id == Employee.LegalEntityId)
    )
    if not include_archived:
        query = query.where(Employee.IsActive.is_(True))
    if search:
        pattern = f"{search}%"
        conditions = [getattr(Employee, f).ilike(pattern) for f in _EMPLOYEE_TEXT_FIELDS]
        conditions += [
            Position.Name.ilike(pattern),
            City.Name.ilike(pattern),
            LegalEntity.Name.ilike(pattern),
        ]
        query = query.where(or_(*conditions))
    return apply_data_scope(query, Employee, user, db)


# Query param value -> column checked for emptiness by the "quick filter"
# chips on the frontend (missing-data at-a-glance panel).
_MISSING_FIELD_COLUMNS = {
    "position": Employee.PositionId,
    "email": Employee.Email,
    "corporate_phone": Employee.CorporatePhone,
    "city": Employee.CityId,
    "legal_entity": Employee.LegalEntityId,
    "salary": Employee.Salary,
}

ViewUser = Annotated[User, Depends(require_permission("EMPLOYEES", "VIEW"))]
CreateUser = Annotated[User, Depends(require_permission("EMPLOYEES", "CREATE"))]
UpdateUser = Annotated[User, Depends(require_permission("EMPLOYEES", "UPDATE"))]
DeleteUser = Annotated[User, Depends(require_permission("EMPLOYEES", "DELETE"))]
ExportUser = Annotated[User, Depends(require_permission("EMPLOYEES", "EXPORT"))]

PII_WRITE_FIELDS = ("IIN", "PersonalPhone")


def _strip_pii_if_unauthorized(db: DbSession, user: User, payload: dict) -> dict:
    """Defense-in-depth: если у пользователя эти поля скрыты/замаскированы на
    чтение (ColumnPermissions), тем более нельзя разрешать их менять на
    запись — не полагаемся на то, что write-право и column-право сегодня
    случайно совпадают для одних и тех же ролей."""
    modes = get_field_modes(db, "Employees", user)
    for field in PII_WRITE_FIELDS:
        if modes.get(field, "FULL") != "FULL":
            payload.pop(field, None)
    return payload


def _check_data_scope_or_404(db: DbSession, user: User, emp: Employee) -> None:
    """Прямой доступ по Id должен уважать те же RLS-границы, что и список
    (§15 ТЗ) — иначе пользователь без доступа к организации мог бы читать
    любую карточку, просто зная/подобрав её Id."""
    from app.services.access import get_accessible_org_unit_ids

    accessible = get_accessible_org_unit_ids(db, user)
    if accessible is None:
        return
    if emp.OrgUnitId is None or emp.OrgUnitId not in accessible:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")


def serialize_employee(db: DbSession, emp: Employee, user: User) -> EmployeeOut:
    data = {
        col.name: getattr(emp, col.name)
        for col in Employee.__table__.columns
    }
    data["CorporateTenure"] = compute_tenure(emp.HireDate, emp.DismissalDate)
    data = apply_field_security("Employees", data, user, db)
    return EmployeeOut(**data)


@router.get("", response_model=Page[EmployeeOut], response_model_exclude_unset=True)
def list_employees(
    db: DbSession,
    user: ViewUser,
    skip: int = 0,
    limit: int = 50,
    search: str | None = None,
    include_archived: bool = False,
    missing_field: str | None = None,
):
    query = build_employee_search_query(db, user, search, include_archived)
    column = _MISSING_FIELD_COLUMNS.get(missing_field) if missing_field else None
    if column is not None:
        query = query.where(column.is_(None))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.offset(skip).limit(limit)).all()
    return Page(
        items=[serialize_employee(db, e, user) for e in items],
        total=total,
        skip=skip,
        limit=limit,
    )


_GENDER_LABELS = {Gender.MALE: "Мужской", Gender.FEMALE: "Женский"}
_STATUS_LABELS = {
    EmployeeStatus.ACTIVE: "Активен",
    EmployeeStatus.ON_LEAVE: "В отпуске",
    EmployeeStatus.DISMISSED: "Уволен",
}


@router.get("/export")
def export_employees(
    db: DbSession,
    user: ExportUser,
    search: str | None = None,
    include_archived: bool = False,
):
    """Экспорт в Excel — уважает текущий фильтр (search/include_archived) как
    и обычный список; если фильтр не задан, выгружает всё. Все столбцы (не
    только видимые на экране через "Столбцы") плюс аттестаты сотрудника,
    свёрнутые в три колонки через "; " (у сотрудника их может быть несколько).
    ИИН/личный телефон маскируются/скрываются по той же ColumnPermissions
    логике, что и в обычном просмотре (§14 ТЗ: "не экспортируется в Excel").
    """
    query = build_employee_search_query(db, user, search, include_archived)
    employees = db.scalars(query).all()

    positions = {p.Id: p.Name for p in db.scalars(select(Position)).all()}
    cities = {c.Id: c.Name for c in db.scalars(select(City)).all()}
    legal_entities = {le.Id: le.Name for le in db.scalars(select(LegalEntity)).all()}
    levels = {lv.Id: lv.Name for lv in db.scalars(select(CertificationLevel)).all()}

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Сотрудники"
    sheet.append([
        "ФИО", "Функциональная должность", "ИИН", "Email",
        "Корпоративный номер", "Личный номер", "Место работы (город)",
        "Дата рождения", "Пол", "Дата приёма", "Корпоративный стаж",
        "ТОО ES/Invecon", "Статус", "Оклад",
        "Номера аттестатов", "Уровни аттестатов", "Даты аттестатов",
    ])

    for emp in employees:
        out = serialize_employee(db, emp, user)
        certs = db.scalars(
            select(EmployeeCertificate).where(
                EmployeeCertificate.EmployeeId == emp.Id,
                EmployeeCertificate.IsActive.is_(True),
            )
        ).all()
        cert_numbers = "; ".join(c.CertificateNumber for c in certs if c.CertificateNumber)
        cert_levels = "; ".join(
            levels.get(c.CertificationLevelId, "") for c in certs if c.CertificationLevelId
        )
        cert_dates = "; ".join(c.IssueDate.isoformat() for c in certs if c.IssueDate)
        tenure = (
            f"{out.CorporateTenure.Years} г. {out.CorporateTenure.Months} мес."
            if out.CorporateTenure
            else ""
        )
        sheet.append([
            out.FullName,
            positions.get(out.PositionId, ""),
            out.IIN or "",
            out.Email or "",
            out.CorporatePhone or "",
            out.PersonalPhone or "",
            cities.get(out.CityId, ""),
            out.BirthDate.isoformat() if out.BirthDate else "",
            _GENDER_LABELS.get(out.Gender, ""),
            out.HireDate.isoformat() if out.HireDate else "",
            tenure,
            legal_entities.get(out.LegalEntityId, ""),
            _STATUS_LABELS.get(out.Status, out.Status),
            float(out.Salary) if out.Salary is not None else "",
            cert_numbers,
            cert_levels,
            cert_dates,
        ])

    log_action(
        db, table_name="Employees", record_id=uuid.uuid4(), action=AuditAction.EXPORT,
        user_id=user.Id, reason=f"Экспорт списка сотрудников (search={search!r})",
    )
    db.commit()

    buffer = BytesIO()
    workbook.save(buffer)
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=employees_export.xlsx"},
    )


@router.get("/stats")
def employee_stats(db: DbSession, user: ViewUser, include_archived: bool = False):
    """Счётчики для панели быстрых фильтров ("Функциональная должность",
    "Email" и т.д.) — сколько активных сотрудников не заполнили то или иное
    поле, чтобы это было видно на чипах ещё до открытия карточки."""
    base_query = apply_data_scope(select(Employee), Employee, user, db)
    if not include_archived:
        base_query = base_query.where(Employee.IsActive.is_(True))
    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0

    counts = {"Total": total}
    for key, column in _MISSING_FIELD_COLUMNS.items():
        missing_query = base_query.where(column.is_(None))
        counts[key] = db.scalar(select(func.count()).select_from(missing_query.subquery())) or 0
    return counts


@router.get("/{item_id}", response_model=EmployeeOut, response_model_exclude_unset=True)
def get_employee(item_id: uuid.UUID, db: DbSession, user: ViewUser):
    obj = repo.get(db, item_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
    _check_data_scope_or_404(db, user, obj)
    return serialize_employee(db, obj, user)


@router.post("", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED, response_model_exclude_unset=True)
def create_employee(data: EmployeeCreate, db: DbSession, user: CreateUser):
    payload = _strip_pii_if_unauthorized(db, user, data.model_dump())
    obj = repo.create(db, payload, user.Id)
    return serialize_employee(db, obj, user)


@router.patch("/{item_id}", response_model=EmployeeOut, response_model_exclude_unset=True)
def update_employee(item_id: uuid.UUID, data: EmployeeUpdate, db: DbSession, user: UpdateUser):
    existing = repo.get(db, item_id)
    if existing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
    _check_data_scope_or_404(db, user, existing)
    payload = _strip_pii_if_unauthorized(db, user, data.model_dump(exclude_unset=True))
    obj = repo.update(db, item_id, payload, user.Id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
    return serialize_employee(db, obj, user)


@router.post("/{item_id}/archive", response_model=EmployeeOut, response_model_exclude_unset=True)
def archive_employee(item_id: uuid.UUID, db: DbSession, user: DeleteUser):
    existing = repo.get(db, item_id)
    if existing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
    _check_data_scope_or_404(db, user, existing)
    obj = repo.archive(db, item_id, user.Id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
    return serialize_employee(db, obj, user)


@router.post("/{item_id}/restore", response_model=EmployeeOut, response_model_exclude_unset=True)
def restore_employee(item_id: uuid.UUID, db: DbSession, user: DeleteUser):
    existing = repo.get(db, item_id)
    if existing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
    _check_data_scope_or_404(db, user, existing)
    obj = repo.restore(db, item_id, user.Id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
    return serialize_employee(db, obj, user)


@router.get("/{item_id}/history", response_model=Page[EmployeeHistoryEntryOut])
def employee_history(
    item_id: uuid.UUID,
    db: DbSession,
    user: ViewUser,
    skip: int = 0,
    limit: int = 50,
):
    existing = repo.get(db, item_id)
    if existing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
    _check_data_scope_or_404(db, user, existing)

    query = (
        select(AuditLog, User.Login)
        .join(User, User.Id == AuditLog.ChangedByUserId, isouter=True)
        .where(AuditLog.TableName == "Employees", AuditLog.RecordId == item_id)
        .order_by(AuditLog.ChangedDate.desc())
    )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(query.offset(skip).limit(limit)).all()

    field_modes = get_field_modes(db, "Employees", user)
    entries = []
    for log, login in rows:
        old_value, new_value = log.OldValue, log.NewValue
        mode = field_modes.get(log.FieldName, "FULL") if log.FieldName else "FULL"
        if mode == "MASKED" and log.FieldName == "IIN":
            old_value, new_value = mask_iin(old_value), mask_iin(new_value)
        elif mode == "HIDDEN":
            old_value, new_value = None, None
        entries.append(
            EmployeeHistoryEntryOut(
                Id=log.Id,
                Action=log.Action,
                ChangedByUserId=log.ChangedByUserId,
                ChangedByLogin=login,
                ChangedDate=log.ChangedDate,
                FieldName=log.FieldName,
                OldValue=old_value,
                NewValue=new_value,
            )
        )
    return Page(items=entries, total=total, skip=skip, limit=limit)
