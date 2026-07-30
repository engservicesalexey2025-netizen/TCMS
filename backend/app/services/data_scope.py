"""Row-Level Security (§15 ТЗ). DataScopes — ручные исключения СВЕРХ двух
уже существующих источников: UserOrgAccess (организации, см.
app/services/access.py) и Assignments (проекты — сотрудник видит только
проекты, на которые назначен). apply_data_scope подключается точечно по
модели через SCOPE_RULES; модели вне карты не фильтруются (сознательный
дефолт "пока не описано — не ограничено", позволяет подключать сущности по
одной, не переписывая всё разом)."""
import uuid
from datetime import datetime, timezone
from typing import Type

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.employee import Employee
from app.models.permission import DataScope
from app.models.project import Project
from app.models.user import User


def _now() -> datetime:
    return datetime.now(timezone.utc)


def get_accessible_project_ids(db: Session, user: User) -> set[uuid.UUID] | None:
    """None = без ограничений (роль с BypassDataScope). Иначе — объединение
    проектов из Assignments сотрудника (если User.EmployeeId задан) и ручных
    DataScopes(ScopeType='PROJECT')."""
    from app.services.permissions import get_active_role_ids
    from app.models.user import Role

    role_ids = get_active_role_ids(db, user)
    if role_ids and db.scalar(
        select(Role.Id).where(Role.Id.in_(role_ids), Role.BypassDataScope.is_(True))
    ):
        return None

    project_ids: set[uuid.UUID] = set()
    if user.EmployeeId is not None:
        project_ids |= set(
            db.scalars(
                select(Assignment.ProjectId).where(Assignment.EmployeeId == user.EmployeeId)
            ).all()
        )

    now = _now()
    scope_rows = db.scalars(
        select(DataScope).where(
            DataScope.UserId == user.Id,
            DataScope.ScopeType == "PROJECT",
            DataScope.IsActive.is_(True),
        )
    ).all()
    project_ids |= {
        row.ScopeId for row in scope_rows if row.ExpiresAt is None or row.ExpiresAt > now
    }

    return project_ids


# Модель -> (тип ограничения, колонка модели, по которой фильтруем).
# 'org'     -> apply_data_scope сравнивает колонку с get_accessible_org_unit_ids
# 'project' -> apply_data_scope сравнивает колонку с get_accessible_project_ids
SCOPE_RULES: dict[Type, tuple[str, str]] = {
    Employee: ("org", "OrgUnitId"),
    Project: ("org", "OrgUnitId"),
    Assignment: ("project", "ProjectId"),
}


def _resolve_accessible_ids(scope_type: str, user: User, db: Session) -> set[uuid.UUID] | None:
    from app.services.access import get_accessible_org_unit_ids

    if scope_type == "org":
        return get_accessible_org_unit_ids(db, user)
    return get_accessible_project_ids(db, user)


def apply_data_scope(query: Select, model: Type, user: User, db: Session) -> Select:
    """Дополняет query фильтром по доступным строкам, если модель описана в
    SCOPE_RULES. Возвращает query без изменений для остальных моделей."""
    rule = SCOPE_RULES.get(model)
    if rule is None:
        return query

    scope_type, column_name = rule
    column = getattr(model, column_name)
    accessible = _resolve_accessible_ids(scope_type, user, db)
    if accessible is None:
        return query
    return query.where(column.in_(accessible))


def is_in_scope(db: Session, user: User, model: Type, obj) -> bool:
    """Проверка для доступа по одному Id (§15 ТЗ) — те же границы, что и у
    списка, иначе пользователь без доступа к организации/проекту мог бы
    прочитать запись напрямую, просто зная её Id."""
    rule = SCOPE_RULES.get(model)
    if rule is None:
        return True

    scope_type, column_name = rule
    accessible = _resolve_accessible_ids(scope_type, user, db)
    if accessible is None:
        return True

    value = getattr(obj, column_name)
    return value is not None and value in accessible
