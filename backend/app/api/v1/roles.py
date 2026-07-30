"""«Конструктор прав доступа» (§16 ТЗ) — управление ролями, правами по
модулям и правами по столбцам. Всё защищено require_superadmin(), а не
гранулярными правами: иначе администратор рискует случайно отобрать у себя
же доступ к экрану, которым это чинится."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession, require_superadmin
from app.models.enums import AuditAction
from app.models.permission import ColumnPermission, Permission, RolePermission
from app.models.user import Role, User
from app.schemas.common import Page
from app.schemas.roles_admin import (
    ColumnPermissionEntryOut,
    ColumnPermissionsIn,
    PermissionGrantIn,
    PermissionMatrixEntryOut,
    RoleAdminOut,
    RoleCloneIn,
    RoleCreateIn,
    RoleUpdateIn,
)
from app.services.audit import log_action

router = APIRouter(prefix="/roles", tags=["roles"])

SuperAdmin = Depends(require_superadmin())


@router.get("", response_model=Page[RoleAdminOut])
def list_roles(db: DbSession, _admin: User = SuperAdmin, skip: int = 0, limit: int = 100) -> Page:
    query = select(Role)
    total = len(db.scalars(query).all())
    rows = db.scalars(query.offset(skip).limit(limit)).all()
    return Page(items=[RoleAdminOut.model_validate(r) for r in rows], total=total, skip=skip, limit=limit)


@router.post("", response_model=RoleAdminOut, status_code=status.HTTP_201_CREATED)
def create_role(data: RoleCreateIn, db: DbSession, admin: User = SuperAdmin) -> Role:
    if db.scalar(select(Role).where(Role.Code == data.Code)):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Код роли '{data.Code}' уже используется")
    role = Role(Code=data.Code, Name=data.Name, CreatedBy=admin.Id, ModifiedBy=admin.Id)
    db.add(role)
    db.flush()
    log_action(db, table_name="Roles", record_id=role.Id, action=AuditAction.CREATE, user_id=admin.Id)
    db.commit()
    db.refresh(role)
    return role


@router.patch("/{role_id}", response_model=RoleAdminOut)
def update_role(role_id: uuid.UUID, data: RoleUpdateIn, db: DbSession, admin: User = SuperAdmin) -> Role:
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Роль не найдена")
    old_name = role.Name
    role.Name = data.Name
    role.ModifiedBy = admin.Id
    log_action(
        db, table_name="Roles", record_id=role.Id, action=AuditAction.UPDATE, user_id=admin.Id,
        field_name="Name", old_value=old_name, new_value=data.Name,
    )
    db.commit()
    db.refresh(role)
    return role


@router.post("/{role_id}/clone", response_model=RoleAdminOut, status_code=status.HTTP_201_CREATED)
def clone_role(role_id: uuid.UUID, data: RoleCloneIn, db: DbSession, admin: User = SuperAdmin) -> Role:
    """Шаблоны ролей (доп. рекомендация №5 ТЗ): роль сама по себе и есть
    шаблон — клонируем её действующие RolePermissions/ColumnPermissions."""
    source = db.get(Role, role_id)
    if source is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Роль-донор не найдена")
    if db.scalar(select(Role).where(Role.Code == data.NewCode)):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Код роли '{data.NewCode}' уже используется")

    new_role = Role(Code=data.NewCode, Name=data.NewName, CreatedBy=admin.Id, ModifiedBy=admin.Id)
    db.add(new_role)
    db.flush()

    source_permissions = db.scalars(
        select(RolePermission).where(RolePermission.RoleId == source.Id, RolePermission.IsActive.is_(True))
    ).all()
    for rp in source_permissions:
        db.add(RolePermission(RoleId=new_role.Id, PermissionId=rp.PermissionId, CreatedBy=admin.Id, ModifiedBy=admin.Id))

    source_columns = db.scalars(
        select(ColumnPermission).where(ColumnPermission.RoleId == source.Id, ColumnPermission.IsActive.is_(True))
    ).all()
    for cp in source_columns:
        db.add(
            ColumnPermission(
                EntityName=cp.EntityName, FieldName=cp.FieldName, RoleId=new_role.Id, Mode=cp.Mode,
                CreatedBy=admin.Id, ModifiedBy=admin.Id,
            )
        )

    log_action(
        db, table_name="Roles", record_id=new_role.Id, action=AuditAction.CREATE, user_id=admin.Id,
        reason=f"Клонирована из роли {source.Code}",
    )
    db.commit()
    db.refresh(new_role)
    return new_role


@router.get("/{role_id}/permissions", response_model=list[PermissionMatrixEntryOut])
def get_role_permissions(role_id: uuid.UUID, db: DbSession, _admin: User = SuperAdmin) -> list[PermissionMatrixEntryOut]:
    if db.get(Role, role_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Роль не найдена")

    granted_ids = set(
        db.scalars(
            select(RolePermission.PermissionId).where(
                RolePermission.RoleId == role_id, RolePermission.IsActive.is_(True)
            )
        ).all()
    )
    permissions = db.scalars(select(Permission).order_by(Permission.Module, Permission.Action)).all()
    return [
        PermissionMatrixEntryOut(Module=p.Module, Action=p.Action, Granted=p.Id in granted_ids)
        for p in permissions
    ]


@router.put("/{role_id}/permissions", response_model=list[PermissionMatrixEntryOut])
def set_role_permissions(
    role_id: uuid.UUID, grants: list[PermissionGrantIn], db: DbSession, admin: User = SuperAdmin
) -> list[PermissionMatrixEntryOut]:
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Роль не найдена")

    existing = {
        rp.PermissionId: rp
        for rp in db.scalars(select(RolePermission).where(RolePermission.RoleId == role_id)).all()
    }
    changed = False
    for grant in grants:
        permission_id = db.scalar(
            select(Permission.Id).where(Permission.Module == grant.Module, Permission.Action == grant.Action)
        )
        if permission_id is None:
            continue
        row = existing.get(permission_id)
        if grant.Granted:
            if row is None:
                db.add(RolePermission(RoleId=role_id, PermissionId=permission_id, CreatedBy=admin.Id, ModifiedBy=admin.Id))
                changed = True
            elif not row.IsActive:
                row.IsActive = True
                row.ModifiedBy = admin.Id
                changed = True
        else:
            if row is not None and row.IsActive:
                row.IsActive = False
                row.ModifiedBy = admin.Id
                changed = True

    if changed:
        log_action(
            db, table_name="RolePermissions", record_id=role_id, action=AuditAction.UPDATE, user_id=admin.Id,
            reason=f"Изменены права роли {role.Code}",
        )
    db.commit()
    return get_role_permissions(role_id, db, admin)


@router.get("/{role_id}/column-permissions", response_model=list[ColumnPermissionEntryOut])
def get_role_column_permissions(
    role_id: uuid.UUID, entity: str, db: DbSession, _admin: User = SuperAdmin
) -> list[ColumnPermissionEntryOut]:
    if db.get(Role, role_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Роль не найдена")
    rows = db.scalars(
        select(ColumnPermission).where(
            ColumnPermission.RoleId == role_id,
            ColumnPermission.EntityName == entity,
            ColumnPermission.IsActive.is_(True),
        )
    ).all()
    return [ColumnPermissionEntryOut(FieldName=r.FieldName, Mode=r.Mode) for r in rows]


@router.put("/{role_id}/column-permissions", response_model=list[ColumnPermissionEntryOut])
def set_role_column_permissions(
    role_id: uuid.UUID, data: ColumnPermissionsIn, db: DbSession, admin: User = SuperAdmin
) -> list[ColumnPermissionEntryOut]:
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Роль не найдена")

    existing = {
        r.FieldName: r
        for r in db.scalars(
            select(ColumnPermission).where(
                ColumnPermission.RoleId == role_id, ColumnPermission.EntityName == data.EntityName
            )
        ).all()
    }
    desired = {f.FieldName: f.Mode for f in data.Fields}

    for field_name, mode in desired.items():
        row = existing.get(field_name)
        if mode == "FULL":
            if row is not None and row.IsActive:
                row.IsActive = False
                row.ModifiedBy = admin.Id
        elif row is None:
            db.add(
                ColumnPermission(
                    EntityName=data.EntityName, FieldName=field_name, RoleId=role_id, Mode=mode,
                    CreatedBy=admin.Id, ModifiedBy=admin.Id,
                )
            )
        else:
            row.Mode = mode
            row.IsActive = True
            row.ModifiedBy = admin.Id

    for field_name, row in existing.items():
        if field_name not in desired and row.IsActive:
            row.IsActive = False
            row.ModifiedBy = admin.Id

    log_action(
        db, table_name="ColumnPermissions", record_id=role_id, action=AuditAction.UPDATE, user_id=admin.Id,
        reason=f"Изменены права на столбцы «{data.EntityName}» для роли {role.Code}",
    )
    db.commit()
    return get_role_column_permissions(role_id, data.EntityName, db, admin)
