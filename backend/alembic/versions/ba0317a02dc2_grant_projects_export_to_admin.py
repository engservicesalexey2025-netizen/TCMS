"""grant projects export to admin

Revision ID: ba0317a02dc2
Revises: c7100f3c0eda
Create Date: 2026-07-29 16:20:00.000000

Изначальный сид (624d94285cfc) дал EXPORT только на EMPLOYEES (чувствительные
персональные данные) — по той же логике «минимум прав по умолчанию,
администратор расширяет через Конструктор» экспорт Проектов тоже сначала
ограничивается ADMIN, а не остаётся открытым всем аутентифицированным, как
было исторически до модуля доступа.
"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ba0317a02dc2'
down_revision: Union[str, None] = 'c7100f3c0eda'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    permission_id = bind.execute(
        sa.text('SELECT "Id" FROM "Permissions" WHERE "Module" = :m AND "Action" = :a'),
        {"m": "PROJECTS", "a": "EXPORT"},
    ).scalar()
    admin_role_id = bind.execute(
        sa.text('SELECT "Id" FROM "Roles" WHERE "Code" = :code'), {"code": "ADMIN"}
    ).scalar()
    if permission_id is None or admin_role_id is None:
        return

    already_granted = bind.execute(
        sa.text(
            'SELECT 1 FROM "RolePermissions" WHERE "RoleId" = :r AND "PermissionId" = :p'
        ),
        {"r": admin_role_id, "p": permission_id},
    ).scalar()
    if already_granted:
        return

    role_permission_table = sa.table(
        "RolePermissions",
        sa.column("Id", sa.UUID()),
        sa.column("RoleId", sa.UUID()),
        sa.column("PermissionId", sa.UUID()),
        sa.column("IsActive", sa.Boolean()),
        sa.column("Version", sa.Integer()),
    )
    op.bulk_insert(role_permission_table, [{
        "Id": uuid.uuid4(), "RoleId": admin_role_id, "PermissionId": permission_id,
        "IsActive": True, "Version": 1,
    }])


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            'DELETE FROM "RolePermissions" WHERE "RoleId" = (SELECT "Id" FROM "Roles" WHERE "Code" = \'ADMIN\') '
            'AND "PermissionId" = (SELECT "Id" FROM "Permissions" WHERE "Module" = \'PROJECTS\' AND "Action" = \'EXPORT\')'
        )
    )
