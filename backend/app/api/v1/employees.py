import uuid
from io import BytesIO
from typing import Annotated

import openpyxl
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, or_, select

from app.api.deps import CurrentUser, DbSession, require_roles
from app.models.audit import AuditLog
from app.models.employee import Employee
from app.models.employee_certificate import CertificationLevel, EmployeeCertificate
from app.models.enums import EmployeeStatus, Gender, RoleCode
from app.models.org import City, LegalEntity, Position
from app.models.user import User
from app.schemas.common import Page
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeHistoryEntryOut,
    EmployeeOut,
    EmployeeUpdate,
)
from app.services.crud_base import AuditedRepository
from app.services.masking import can_see_full_pii, mask_iin, serialize_employee

router = APIRouter(prefix="/employees", tags=["employees"])

repo = AuditedRepository(Employee, search_fields=["FullName", "Email", "IIN"])

# Text columns living directly on Employees, searched by prefix ("по начальным
# буквам") — covers everything the generic AuditedRepository.list() can reach
# without a join.
_EMPLOYEE_TEXT_FIELDS = ["FullName", "Email", "IIN", "CorporatePhone", "PersonalPhone"]


def build_employee_search_query(search: str | None, include_archived: bool):
    """Shared by list_employees and the Excel export: prefix-matches `search`
    across every employee-facing column shown in the table, including the
    resolved reference labels (Position/City/LegalEntity), which requires a
    join — the generic AuditedRepository.list() only searches raw columns on
    the entity's own table, so this bypasses it for Employees specifically.
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
    return query
WRITE_ROLES = (RoleCode.ADMIN, RoleCode.DEPARTMENT_HEAD, RoleCode.GROUP_HEAD)
WriteUser = Annotated[User, Depends(require_roles(*WRITE_ROLES))]

# WRITE_ROLES happens to equal masking.FULL_PII_ROLES today — the strip below
# is defense-in-depth so a future change to either set doesn't silently open
# a write path to IIN/PersonalPhone for a role that can't even see them.
PII_WRITE_FIELDS = ("IIN", "PersonalPhone")


def _strip_pii_if_unauthorized(user: User, payload: dict) -> dict:
    if not can_see_full_pii(user):
        for field in PII_WRITE_FIELDS:
            payload.pop(field, None)
    return payload


@router.get("", response_model=Page[EmployeeOut])
def list_employees(
    db: DbSession,
    user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
    search: str | None = None,
    include_archived: bool = False,
):
    query = build_employee_search_query(search, include_archived)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.offset(skip).limit(limit)).all()
    return Page(
        items=[serialize_employee(e, user) for e in items],
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
    user: CurrentUser,
    search: str | None = None,
    include_archived: bool = False,
):
    """Экспорт в Excel — уважает текущий фильтр (search/include_archived) как
    и обычный список; если фильтр не задан, выгружает всё. Все столбцы (не
    только видимые на экране через "Столбцы") плюс аттестаты сотрудника,
    свёрнутые в три колонки через "; " (у сотрудника их может быть несколько).
    ИИН/личный телефон маскируются по той же роли, что и в обычном просмотре.
    """
    query = build_employee_search_query(search, include_archived)
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
        "ТОО ES/Invecon", "Статус",
        "Номера аттестатов", "Уровни аттестатов", "Даты аттестатов",
    ])

    for emp in employees:
        out = serialize_employee(emp, user)
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
            cert_numbers,
            cert_levels,
            cert_dates,
        ])

    buffer = BytesIO()
    workbook.save(buffer)
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=employees_export.xlsx"},
    )


@router.get("/{item_id}", response_model=EmployeeOut)
def get_employee(item_id: uuid.UUID, db: DbSession, user: CurrentUser):
    obj = repo.get(db, item_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
    return serialize_employee(obj, user)


@router.post("", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
def create_employee(data: EmployeeCreate, db: DbSession, user: WriteUser):
    payload = _strip_pii_if_unauthorized(user, data.model_dump())
    obj = repo.create(db, payload, user.Id)
    return serialize_employee(obj, user)


@router.patch("/{item_id}", response_model=EmployeeOut)
def update_employee(item_id: uuid.UUID, data: EmployeeUpdate, db: DbSession, user: WriteUser):
    payload = _strip_pii_if_unauthorized(user, data.model_dump(exclude_unset=True))
    obj = repo.update(db, item_id, payload, user.Id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
    return serialize_employee(obj, user)


@router.post("/{item_id}/archive", response_model=EmployeeOut)
def archive_employee(item_id: uuid.UUID, db: DbSession, user: WriteUser):
    obj = repo.archive(db, item_id, user.Id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
    return serialize_employee(obj, user)


@router.post("/{item_id}/restore", response_model=EmployeeOut)
def restore_employee(item_id: uuid.UUID, db: DbSession, user: WriteUser):
    obj = repo.restore(db, item_id, user.Id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
    return serialize_employee(obj, user)


@router.get("/{item_id}/history", response_model=Page[EmployeeHistoryEntryOut])
def employee_history(
    item_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
):
    if repo.get(db, item_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")

    query = (
        select(AuditLog, User.Login)
        .join(User, User.Id == AuditLog.ChangedByUserId, isouter=True)
        .where(AuditLog.TableName == "Employees", AuditLog.RecordId == item_id)
        .order_by(AuditLog.ChangedDate.desc())
    )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(query.offset(skip).limit(limit)).all()

    masked = not can_see_full_pii(user)
    entries = []
    for log, login in rows:
        old_value, new_value = log.OldValue, log.NewValue
        if masked and log.FieldName == "IIN":
            old_value, new_value = mask_iin(old_value), mask_iin(new_value)
        elif masked and log.FieldName == "PersonalPhone":
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
