"""seed users module permissions

Revision ID: f9779e672f8f
Revises: d9a25fefcb05
Create Date: 2026-07-29 16:00:00.000000

Модуль USERS не попал в первичный посев (624d94285cfc) — понадобился при
реализации auth.py: сброс пароля администратором и «Просмотреть как
пользователь» (§12, доп. рекомендация №4 ТЗ) — это права над учётными
записями, а не над бизнес-разделами.
"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f9779e672f8f'
down_revision: Union[str, None] = 'd9a25fefcb05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ACTIONS = ["VIEW", "CREATE", "UPDATE", "DELETE", "VIEW_AS"]
ACTION_NAMES = {
    "VIEW": "Просмотр", "CREATE": "Создание", "UPDATE": "Изменение",
    "DELETE": "Удаление", "VIEW_AS": "Просмотреть как пользователь",
}


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
            "Id": pid, "Module": "USERS", "Action": action,
            "Code": f"USERS.{action}", "Name": f"{ACTION_NAMES[action]} — USERS",
            "IsActive": True, "Version": 1,
        })
    op.bulk_insert(permission_table, rows)

    admin_role_id = bind.execute(
        sa.text('SELECT "Id" FROM "Roles" WHERE "Code" = :code'), {"code": "ADMIN"}
    ).scalar()

    role_permission_table = sa.table(
        "RolePermissions",
        sa.column("Id", sa.UUID()),
        sa.column("RoleId", sa.UUID()),
        sa.column("PermissionId", sa.UUID()),
        sa.column("IsActive", sa.Boolean()),
        sa.column("Version", sa.Integer()),
    )
    if admin_role_id is not None:
        op.bulk_insert(role_permission_table, [
            {"Id": uuid.uuid4(), "RoleId": admin_role_id, "PermissionId": pid, "IsActive": True, "Version": 1}
            for pid in permission_ids.values()
        ])


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            'DELETE FROM "RolePermissions" WHERE "PermissionId" IN '
            '(SELECT "Id" FROM "Permissions" WHERE "Module" = \'USERS\')'
        )
    )
    bind.execute(sa.text('DELETE FROM "Permissions" WHERE "Module" = \'USERS\''))
