"""seed security log permission

Revision ID: c7100f3c0eda
Revises: f9779e672f8f
Create Date: 2026-07-29 16:10:00.000000

Журнал безопасности (§17 ТЗ) — отдельный модуль прав, доступный по
умолчанию только ADMIN.
"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c7100f3c0eda'
down_revision: Union[str, None] = 'f9779e672f8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    permission_id = uuid.uuid4()
    permission_table = sa.table(
        "Permissions",
        sa.column("Id", sa.UUID()),
        sa.column("Module", sa.String()),
        sa.column("Action", sa.String()),
        sa.column("Code", sa.String()),
        sa.column("Name", sa.String()),
        sa.column("IsActive", sa.Boolean()),
        sa.column("Version", sa.Integer()),
    )
    op.bulk_insert(permission_table, [{
        "Id": permission_id, "Module": "SECURITY_LOG", "Action": "VIEW",
        "Code": "SECURITY_LOG.VIEW", "Name": "Просмотр — журнал безопасности",
        "IsActive": True, "Version": 1,
    }])

    admin_role_id = bind.execute(
        sa.text('SELECT "Id" FROM "Roles" WHERE "Code" = :code'), {"code": "ADMIN"}
    ).scalar()
    if admin_role_id is not None:
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
            'DELETE FROM "RolePermissions" WHERE "PermissionId" IN '
            '(SELECT "Id" FROM "Permissions" WHERE "Module" = \'SECURITY_LOG\')'
        )
    )
    bind.execute(sa.text('DELETE FROM "Permissions" WHERE "Module" = \'SECURITY_LOG\''))
