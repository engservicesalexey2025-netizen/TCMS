"""seed kpi settings module

Revision ID: b13003ffdb79
Revises: ba0317a02dc2
Create Date: 2026-07-29 16:25:00.000000

KPI-настройки (коэффициенты формулы) сегодня редактируются строже, чем
норм-матрица (ADMIN-only vs ADMIN+DEPARTMENT_HEAD) — отдельный модуль
прав, а не общий KPI, иначе это различие потерялось бы при переходе на
require_permission.
"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b13003ffdb79'
down_revision: Union[str, None] = 'ba0317a02dc2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ACTIONS = ["VIEW", "UPDATE"]
ACTION_NAMES = {"VIEW": "Просмотр", "UPDATE": "Изменение"}


def upgrade() -> None:
    bind = op.get_bind()
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
    permission_ids = {}
    rows = []
    for action in ACTIONS:
        pid = uuid.uuid4()
        permission_ids[action] = pid
        rows.append({
            "Id": pid, "Module": "KPI_SETTINGS", "Action": action,
            "Code": f"KPI_SETTINGS.{action}", "Name": f"{ACTION_NAMES[action]} — KPI_SETTINGS",
            "IsActive": True, "Version": 1,
        })
    op.bulk_insert(permission_table, rows)

    role_permission_table = sa.table(
        "RolePermissions",
        sa.column("Id", sa.UUID()),
        sa.column("RoleId", sa.UUID()),
        sa.column("PermissionId", sa.UUID()),
        sa.column("IsActive", sa.Boolean()),
        sa.column("Version", sa.Integer()),
    )
    role_rows = []
    for role_code in ("ADMIN", "DIVISION_DIRECTOR", "DEPARTMENT_HEAD", "GROUP_HEAD", "OBSERVER"):
        role_id = bind.execute(
            sa.text('SELECT "Id" FROM "Roles" WHERE "Code" = :code'), {"code": role_code}
        ).scalar()
        if role_id is None:
            continue
        role_rows.append({
            "Id": uuid.uuid4(), "RoleId": role_id, "PermissionId": permission_ids["VIEW"],
            "IsActive": True, "Version": 1,
        })
    admin_role_id = bind.execute(
        sa.text('SELECT "Id" FROM "Roles" WHERE "Code" = :code'), {"code": "ADMIN"}
    ).scalar()
    if admin_role_id is not None:
        role_rows.append({
            "Id": uuid.uuid4(), "RoleId": admin_role_id, "PermissionId": permission_ids["UPDATE"],
            "IsActive": True, "Version": 1,
        })
    op.bulk_insert(role_permission_table, role_rows)


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            'DELETE FROM "RolePermissions" WHERE "PermissionId" IN '
            '(SELECT "Id" FROM "Permissions" WHERE "Module" = \'KPI_SETTINGS\')'
        )
    )
    bind.execute(sa.text('DELETE FROM "Permissions" WHERE "Module" = \'KPI_SETTINGS\''))
