"""Центральная проверка прав (§13/§16 ТЗ) — заменяет плоский require_roles().

Порядок проверки в user_has_permission (первое совпадение решает):
  1. UserPermission(Effect=DENY) на пользователя  -> False (побеждает всё)
  2. UserPermission(Effect=GRANT) на пользователя  -> True
  3. RolePermission любой активной роли пользователя -> True
  4. Входящие активные Delegation (без транзитивности, один шаг) -> проверить
     то же самое для FromUser
  5. иначе -> False
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import Delegation, Permission, RolePermission, UserPermission, UserRole
from app.models.user import User


def _now() -> datetime:
    return datetime.now(timezone.utc)


def get_active_role_ids(db: Session, user: User) -> set[uuid.UUID]:
    """Активные (не истёкшие) роли пользователя из UserRoles."""
    rows = db.scalars(
        select(UserRole).where(UserRole.UserId == user.Id, UserRole.IsActive.is_(True))
    ).all()
    now = _now()
    return {r.RoleId for r in rows if r.ExpiresAt is None or r.ExpiresAt > now}


def _permission_id(db: Session, module: str, action: str) -> uuid.UUID | None:
    return db.scalar(
        select(Permission.Id).where(Permission.Module == module, Permission.Action == action)
    )


def _direct_user_effect(db: Session, user_id: uuid.UUID, permission_id: uuid.UUID) -> str | None:
    now = _now()
    row = db.scalar(
        select(UserPermission).where(
            UserPermission.UserId == user_id,
            UserPermission.PermissionId == permission_id,
            UserPermission.IsActive.is_(True),
        )
    )
    if row is None:
        return None
    if row.ExpiresAt is not None and row.ExpiresAt <= now:
        return None
    return row.Effect


def _role_grants(db: Session, role_ids: set[uuid.UUID], permission_id: uuid.UUID) -> bool:
    if not role_ids:
        return False
    return (
        db.scalar(
            select(RolePermission.Id).where(
                RolePermission.RoleId.in_(role_ids),
                RolePermission.PermissionId == permission_id,
                RolePermission.IsActive.is_(True),
            )
        )
        is not None
    )


def _user_grants_permission(db: Session, user_id: uuid.UUID, permission_id: uuid.UUID) -> bool | None:
    """True/False если для этого пользователя есть окончательный вердикт
    (DENY или GRANT/роль), None если решение не найдено на его уровне."""
    effect = _direct_user_effect(db, user_id, permission_id)
    if effect == "DENY":
        return False
    if effect == "GRANT":
        return True

    role_ids = get_active_role_ids(db, db.get(User, user_id))
    if _role_grants(db, role_ids, permission_id):
        return True
    return None


# Соответствие Module (право) -> EntityName (ColumnPermissions/AuditLog) для
# сущностей, где колоночная безопасность уже подключена. Расширяется по мере
# миграции остальных роутеров на field_security.
MODULE_TO_ENTITY_NAME = {"EMPLOYEES": "Employees"}


def get_permission_summary(db: Session, user: User) -> dict[str, dict[str, list[str]]]:
    """Сводка для GET /auth/me: {Module: {actions: [...], columns: [...]}}.
    `columns` — список полей, СКРЫТЫХ (Mode=HIDDEN) для пользователя на этой
    сущности (не полный список видимых — у бэкенда нет канонического
    перечня полей сущности, он есть только у фронтенда); пустой список
    значит «ничего дополнительно не скрыто»."""
    from app.services.field_security import get_field_modes

    role_ids = get_active_role_ids(db, user)
    now = _now()

    denied_permission_ids = {
        row.PermissionId
        for row in db.scalars(
            select(UserPermission).where(
                UserPermission.UserId == user.Id,
                UserPermission.Effect == "DENY",
                UserPermission.IsActive.is_(True),
            )
        ).all()
        if row.ExpiresAt is None or row.ExpiresAt > now
    }
    granted_permission_ids = {
        row.PermissionId
        for row in db.scalars(
            select(UserPermission).where(
                UserPermission.UserId == user.Id,
                UserPermission.Effect == "GRANT",
                UserPermission.IsActive.is_(True),
            )
        ).all()
        if row.ExpiresAt is None or row.ExpiresAt > now
    } - denied_permission_ids

    role_permission_ids = set()
    if role_ids:
        role_permission_ids = set(
            db.scalars(
                select(RolePermission.PermissionId).where(
                    RolePermission.RoleId.in_(role_ids),
                    RolePermission.IsActive.is_(True),
                )
            ).all()
        )
    effective_ids = (role_permission_ids | granted_permission_ids) - denied_permission_ids
    if not effective_ids:
        return {}

    permissions = db.scalars(select(Permission).where(Permission.Id.in_(effective_ids))).all()
    summary: dict[str, dict[str, list[str]]] = {}
    for perm in permissions:
        summary.setdefault(perm.Module, {"actions": [], "columns": []})
        summary[perm.Module]["actions"].append(perm.Action)

    for module, entity_name in MODULE_TO_ENTITY_NAME.items():
        if module not in summary:
            continue
        modes = get_field_modes(db, entity_name, user)
        summary[module]["columns"] = [
            field for field, mode in modes.items() if mode == "HIDDEN"
        ]

    return summary


def user_has_permission(db: Session, user: User, module: str, action: str) -> bool:
    permission_id = _permission_id(db, module, action)
    if permission_id is None:
        return False

    direct_effect = _direct_user_effect(db, user.Id, permission_id)
    if direct_effect == "DENY":
        return False
    if direct_effect == "GRANT":
        return True

    role_ids = get_active_role_ids(db, user)
    if _role_grants(db, role_ids, permission_id):
        return True

    now = _now()
    delegations = db.scalars(
        select(Delegation).where(
            Delegation.ToUserId == user.Id,
            Delegation.IsActive.is_(True),
            Delegation.StartsAt <= now,
            Delegation.ExpiresAt > now,
        )
    ).all()
    for delegation in delegations:
        from_user = db.get(User, delegation.FromUserId)
        if from_user is None:
            continue
        from_role_ids = get_active_role_ids(db, from_user)
        if delegation.RoleId is not None:
            # делегирована конкретная роль — она должна реально быть у
            # делегирующего, иначе делегирование становится обходом системы прав
            if delegation.RoleId in from_role_ids and _role_grants(
                db, {delegation.RoleId}, permission_id
            ):
                return True
            continue
        if _user_grants_permission(db, delegation.FromUserId, permission_id):
            return True

    return False
