"""seed column permissions

Revision ID: d55d7156c5e4
Revises: 27134ff69e0b
Create Date: 2026-07-29 15:20:00.000000

Воспроизводит сегодняшнее поведение masking.py::FULL_PII_ROLES 1-в-1: ИИН —
маскирован, PersonalPhone — скрыт для ролей вне {ADMIN, DEPARTMENT_HEAD,
GROUP_HEAD}, т.е. для DIVISION_DIRECTOR и OBSERVER.
"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd55d7156c5e4'
down_revision: Union[str, None] = '27134ff69e0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

RESTRICTED_ROLES = ("DIVISION_DIRECTOR", "OBSERVER")


def upgrade() -> None:
    bind = op.get_bind()
    column_permission_table = sa.table(
        "ColumnPermissions",
        sa.column("Id", sa.UUID()),
        sa.column("EntityName", sa.String()),
        sa.column("FieldName", sa.String()),
        sa.column("RoleId", sa.UUID()),
        sa.column("Mode", sa.String()),
        sa.column("IsActive", sa.Boolean()),
        sa.column("Version", sa.Integer()),
    )

    rows = []
    for role_code in RESTRICTED_ROLES:
        role_id = bind.execute(
            sa.text('SELECT "Id" FROM "Roles" WHERE "Code" = :code'), {"code": role_code}
        ).scalar()
        if role_id is None:
            continue
        rows.append({
            "Id": uuid.uuid4(), "EntityName": "Employees", "FieldName": "IIN",
            "RoleId": role_id, "Mode": "MASKED", "IsActive": True, "Version": 1,
        })
        rows.append({
            "Id": uuid.uuid4(), "EntityName": "Employees", "FieldName": "PersonalPhone",
            "RoleId": role_id, "Mode": "HIDDEN", "IsActive": True, "Version": 1,
        })
    op.bulk_insert(column_permission_table, rows)


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            'DELETE FROM "ColumnPermissions" WHERE "EntityName" = \'Employees\' '
            'AND "FieldName" IN (\'IIN\', \'PersonalPhone\')'
        )
    )
