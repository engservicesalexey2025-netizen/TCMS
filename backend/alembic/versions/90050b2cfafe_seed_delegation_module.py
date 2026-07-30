"""seed delegation module

Revision ID: 90050b2cfafe
Revises: a117eb778137
Create Date: 2026-07-29 16:40:00.000000

Делегирование полномочий (доп. рекомендация №3 ТЗ) — «руководитель может
временно передать свои права заместителю»: право делегировать даётся
руководящим ролям, не всем подряд.
"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '90050b2cfafe'
down_revision: Union[str, None] = 'a117eb778137'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

GRANTED_ROLES = ("ADMIN", "DEPARTMENT_HEAD", "GROUP_HEAD")


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
        "Id": permission_id, "Module": "DELEGATION", "Action": "CREATE",
        "Code": "DELEGATION.CREATE", "Name": "Делегирование полномочий",
        "IsActive": True, "Version": 1,
    }])

    role_permission_table = sa.table(
        "RolePermissions",
        sa.column("Id", sa.UUID()),
        sa.column("RoleId", sa.UUID()),
        sa.column("PermissionId", sa.UUID()),
        sa.column("IsActive", sa.Boolean()),
        sa.column("Version", sa.Integer()),
    )
    rows = []
    for role_code in GRANTED_ROLES:
        role_id = bind.execute(
            sa.text('SELECT "Id" FROM "Roles" WHERE "Code" = :code'), {"code": role_code}
        ).scalar()
        if role_id is None:
            continue
        rows.append({"Id": uuid.uuid4(), "RoleId": role_id, "PermissionId": permission_id, "IsActive": True, "Version": 1})
    if rows:
        op.bulk_insert(role_permission_table, rows)


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            'DELETE FROM "RolePermissions" WHERE "PermissionId" IN '
            '(SELECT "Id" FROM "Permissions" WHERE "Module" = \'DELEGATION\')'
        )
    )
    bind.execute(sa.text('DELETE FROM "Permissions" WHERE "Module" = \'DELEGATION\''))
