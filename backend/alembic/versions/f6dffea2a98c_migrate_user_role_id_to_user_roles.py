"""migrate user role id to user roles

Revision ID: f6dffea2a98c
Revises: d55d7156c5e4
Create Date: 2026-07-29 15:25:00.000000

Переносит существующие Users.RoleId в новую многие-ко-многим UserRoles,
построчно, без потерь. Users.RoleId сама колонка НЕ удаляется здесь — это
отдельная, более поздняя миграция, после того как весь код перестанет читать
user.Role.Code (см. финальную уборку модуля доступа).
"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6dffea2a98c'
down_revision: Union[str, None] = 'd55d7156c5e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = bind.execute(sa.text('SELECT "Id", "RoleId" FROM "Users"')).fetchall()

    user_role_table = sa.table(
        "UserRoles",
        sa.column("Id", sa.UUID()),
        sa.column("UserId", sa.UUID()),
        sa.column("RoleId", sa.UUID()),
        sa.column("IsActive", sa.Boolean()),
        sa.column("Version", sa.Integer()),
    )
    rows = [
        {"Id": uuid.uuid4(), "UserId": user_id, "RoleId": role_id, "IsActive": True, "Version": 1}
        for user_id, role_id in existing
    ]
    if rows:
        op.bulk_insert(user_role_table, rows)


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text('DELETE FROM "UserRoles"'))
