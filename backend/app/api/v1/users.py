"""Управление пользователями: список, назначение ролей, персональные
исключения (UserPermissions), доступ по организациям/проектам (§5/§13/§15
ТЗ). Права над этим экраном — модуль USERS, не ROLES: администрирование
конкретных учётных записей отделено от конструктора самих ролей/прав."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession, require_permission
from app.models.enums import AuditAction
from app.models.org import OrgUnit
from app.models.permission import DataScope, Permission, UserPermission, UserRole
from app.models.user import Role, User, UserOrgAccess
from app.schemas.common import Page
from app.schemas.roles_admin import (
    UserDataScopeIn,
    UserDataScopeOut,
    UserDetailOut,
    UserOrgAccessIn,
    UserOrgAccessOut,
    UserPermissionOverrideIn,
    UserPermissionOverrideOut,
    UserRoleAssignmentIn,
    UserRoleAssignmentOut,
    UserSummaryOut,
)
from app.services.audit import log_action
from app.services.permissions import get_active_role_ids

router = APIRouter(prefix="/users", tags=["users"])

ViewUsers = Depends(require_permission("USERS", "VIEW"))
UpdateUsers = Depends(require_permission("USERS", "UPDATE"))


@router.get("", response_model=Page[UserSummaryOut])
def list_users(db: DbSession, _user: User = ViewUsers, skip: int = 0, limit: int = 50) -> Page:
    query = select(User)
    total = len(db.scalars(query).all())
    rows = db.scalars(query.offset(skip).limit(limit)).all()
    items = []
    for u in rows:
        role_ids = get_active_role_ids(db, u)
        names = list(db.scalars(select(Role.Name).where(Role.Id.in_(role_ids))).all()) if role_ids else []
        items.append(UserSummaryOut(Id=u.Id, Login=u.Login, Email=u.Email, IsActive=u.IsActive, Roles=names))
    return Page(items=items, total=total, skip=skip, limit=limit)


def _load_user_detail(db: DbSession, user: User) -> UserDetailOut:
    role_rows = db.scalars(
        select(UserRole).where(UserRole.UserId == user.Id, UserRole.IsActive.is_(True))
    ).all()
    roles = []
    for r in role_rows:
        role = db.get(Role, r.RoleId)
        if role is not None:
            roles.append(UserRoleAssignmentOut(RoleId=role.Id, RoleName=role.Name, ExpiresAt=r.ExpiresAt))

    override_rows = db.scalars(
        select(UserPermission).where(UserPermission.UserId == user.Id, UserPermission.IsActive.is_(True))
    ).all()
    overrides = []
    for o in override_rows:
        perm = db.get(Permission, o.PermissionId)
        if perm is not None:
            overrides.append(
                UserPermissionOverrideOut(
                    Module=perm.Module, Action=perm.Action, Effect=o.Effect,
                    ExpiresAt=o.ExpiresAt, Reason=o.Reason,
                )
            )

    org_rows = db.scalars(
        select(UserOrgAccess).where(UserOrgAccess.UserId == user.Id, UserOrgAccess.IsActive.is_(True))
    ).all()
    org_access = []
    for a in org_rows:
        unit = db.get(OrgUnit, a.OrgUnitId)
        if unit is not None:
            org_access.append(UserOrgAccessOut(OrgUnitId=unit.Id, OrgUnitName=unit.Name, ExpiresAt=a.ExpiresAt))

    scope_rows = db.scalars(
        select(DataScope).where(DataScope.UserId == user.Id, DataScope.IsActive.is_(True))
    ).all()
    scopes = [
        UserDataScopeOut(ScopeType=s.ScopeType, ScopeId=s.ScopeId, ExpiresAt=s.ExpiresAt, Reason=s.Reason)
        for s in scope_rows
    ]

    return UserDetailOut(
        Id=user.Id, Login=user.Login, Email=user.Email, IsActive=user.IsActive,
        MustChangePassword=user.MustChangePassword, MfaEnabled=user.MfaEnabled,
        Roles=roles, PermissionOverrides=overrides, OrgAccess=org_access, DataScopes=scopes,
    )


@router.get("/{user_id}", response_model=UserDetailOut)
def get_user(user_id: uuid.UUID, db: DbSession, _user: User = ViewUsers) -> UserDetailOut:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")
    return _load_user_detail(db, user)


@router.put("/{user_id}/roles", response_model=UserDetailOut)
def set_user_roles(
    user_id: uuid.UUID, data: list[UserRoleAssignmentIn], db: DbSession, admin: User = UpdateUsers
) -> UserDetailOut:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")

    existing = {r.RoleId: r for r in db.scalars(select(UserRole).where(UserRole.UserId == user_id)).all()}
    desired = {d.RoleId: d.ExpiresAt for d in data}

    for role_id, expires_at in desired.items():
        row = existing.get(role_id)
        if row is None:
            db.add(UserRole(UserId=user_id, RoleId=role_id, ExpiresAt=expires_at, CreatedBy=admin.Id, ModifiedBy=admin.Id))
        else:
            row.ExpiresAt = expires_at
            row.IsActive = True
            row.ModifiedBy = admin.Id
    for role_id, row in existing.items():
        if role_id not in desired and row.IsActive:
            row.IsActive = False
            row.ModifiedBy = admin.Id

    log_action(
        db, table_name="UserRoles", record_id=user_id, action=AuditAction.UPDATE, user_id=admin.Id,
        reason="Изменены роли пользователя",
    )
    db.commit()
    return _load_user_detail(db, user)


@router.put("/{user_id}/permissions", response_model=UserDetailOut)
def set_user_permission_overrides(
    user_id: uuid.UUID, data: list[UserPermissionOverrideIn], db: DbSession, admin: User = UpdateUsers
) -> UserDetailOut:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")

    existing = {
        r.PermissionId: r
        for r in db.scalars(select(UserPermission).where(UserPermission.UserId == user_id)).all()
    }
    desired: dict[uuid.UUID, UserPermissionOverrideIn] = {}
    for item in data:
        permission_id = db.scalar(
            select(Permission.Id).where(Permission.Module == item.Module, Permission.Action == item.Action)
        )
        if permission_id is not None:
            desired[permission_id] = item

    for permission_id, item in desired.items():
        row = existing.get(permission_id)
        if row is None:
            db.add(
                UserPermission(
                    UserId=user_id, PermissionId=permission_id, Effect=item.Effect,
                    ExpiresAt=item.ExpiresAt, Reason=item.Reason, CreatedBy=admin.Id, ModifiedBy=admin.Id,
                )
            )
        else:
            row.Effect = item.Effect
            row.ExpiresAt = item.ExpiresAt
            row.Reason = item.Reason
            row.IsActive = True
            row.ModifiedBy = admin.Id
    for permission_id, row in existing.items():
        if permission_id not in desired and row.IsActive:
            row.IsActive = False
            row.ModifiedBy = admin.Id

    log_action(
        db, table_name="UserPermissions", record_id=user_id, action=AuditAction.UPDATE, user_id=admin.Id,
        reason="Изменены персональные исключения прав",
    )
    db.commit()
    return _load_user_detail(db, user)


@router.put("/{user_id}/org-access", response_model=UserDetailOut)
def set_user_org_access(
    user_id: uuid.UUID, data: list[UserOrgAccessIn], db: DbSession, admin: User = UpdateUsers
) -> UserDetailOut:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")

    existing = {
        r.OrgUnitId: r
        for r in db.scalars(select(UserOrgAccess).where(UserOrgAccess.UserId == user_id)).all()
    }
    desired = {d.OrgUnitId: d.ExpiresAt for d in data}

    for org_unit_id, expires_at in desired.items():
        row = existing.get(org_unit_id)
        if row is None:
            db.add(
                UserOrgAccess(
                    UserId=user_id, OrgUnitId=org_unit_id, ExpiresAt=expires_at,
                    CreatedBy=admin.Id, ModifiedBy=admin.Id,
                )
            )
        else:
            row.ExpiresAt = expires_at
            row.IsActive = True
            row.ModifiedBy = admin.Id
    for org_unit_id, row in existing.items():
        if org_unit_id not in desired and row.IsActive:
            row.IsActive = False
            row.ModifiedBy = admin.Id

    log_action(
        db, table_name="UserOrgAccess", record_id=user_id, action=AuditAction.UPDATE, user_id=admin.Id,
        reason="Изменён доступ пользователя по организациям",
    )
    db.commit()
    return _load_user_detail(db, user)


@router.put("/{user_id}/data-scopes", response_model=UserDetailOut)
def set_user_data_scopes(
    user_id: uuid.UUID, data: list[UserDataScopeIn], db: DbSession, admin: User = UpdateUsers
) -> UserDetailOut:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")

    existing = {
        (r.ScopeType, r.ScopeId): r
        for r in db.scalars(select(DataScope).where(DataScope.UserId == user_id)).all()
    }
    desired = {(d.ScopeType, d.ScopeId): d for d in data}

    for key, item in desired.items():
        row = existing.get(key)
        if row is None:
            db.add(
                DataScope(
                    UserId=user_id, ScopeType=item.ScopeType, ScopeId=item.ScopeId,
                    ExpiresAt=item.ExpiresAt, Reason=item.Reason,
                    GrantedByUserId=admin.Id, CreatedBy=admin.Id, ModifiedBy=admin.Id,
                )
            )
        else:
            row.ExpiresAt = item.ExpiresAt
            row.Reason = item.Reason
            row.IsActive = True
            row.ModifiedBy = admin.Id
    for key, row in existing.items():
        if key not in desired and row.IsActive:
            row.IsActive = False
            row.ModifiedBy = admin.Id

    log_action(
        db, table_name="DataScopes", record_id=user_id, action=AuditAction.UPDATE, user_id=admin.Id,
        reason="Изменены ограничения по данным пользователя",
    )
    db.commit()
    return _load_user_detail(db, user)
