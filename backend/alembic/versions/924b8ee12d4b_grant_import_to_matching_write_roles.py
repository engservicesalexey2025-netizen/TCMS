"""grant import to matching write roles

Revision ID: 924b8ee12d4b
Revises: b13003ffdb79
Create Date: 2026-07-29 16:30:00.000000

Изначальный сид (624d94285cfc) дал IMPORT только ADMIN на все модули —
остальные роли получили CREATE/UPDATE/DELETE, но не IMPORT. Это
случайно сузило бы сегодняшнее поведение импорта Excel: import_profiles.py
исторически разрешал импорт employees для DEPARTMENT_HEAD/GROUP_HEAD и
импорт projects для DEPARTMENT_HEAD (write_roles тех профилей). Восстанавливаем
это 1-в-1 перед тем, как imports.py переключится на require_permission.
"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '924b8ee12d4b'
down_revision: Union[str, None] = 'b13003ffdb79'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (роль, модуль) — точное соответствие write_roles трёх сегодняшних
# import-профилей (positions/employees/projects).
GRANTS = [
    ("DEPARTMENT_HEAD", "EMPLOYEES"),
    ("GROUP_HEAD", "EMPLOYEES"),
    ("DEPARTMENT_HEAD", "PROJECTS"),
]


def upgrade() -> None:
    bind = op.get_bind()
    role_permission_table = sa.table(
        "RolePermissions",
        sa.column("Id", sa.UUID()),
        sa.column("RoleId", sa.UUID()),
        sa.column("PermissionId", sa.UUID()),
        sa.column("IsActive", sa.Boolean()),
        sa.column("Version", sa.Integer()),
    )
    rows = []
    for role_code, module in GRANTS:
        role_id = bind.execute(
            sa.text('SELECT "Id" FROM "Roles" WHERE "Code" = :code'), {"code": role_code}
        ).scalar()
        permission_id = bind.execute(
            sa.text('SELECT "Id" FROM "Permissions" WHERE "Module" = :m AND "Action" = \'IMPORT\''),
            {"m": module},
        ).scalar()
        if role_id is None or permission_id is None:
            continue
        already = bind.execute(
            sa.text('SELECT 1 FROM "RolePermissions" WHERE "RoleId" = :r AND "PermissionId" = :p'),
            {"r": role_id, "p": permission_id},
        ).scalar()
        if already:
            continue
        rows.append({"Id": uuid.uuid4(), "RoleId": role_id, "PermissionId": permission_id, "IsActive": True, "Version": 1})
    if rows:
        op.bulk_insert(role_permission_table, rows)


def downgrade() -> None:
    bind = op.get_bind()
    for role_code, module in GRANTS:
        bind.execute(
            sa.text(
                'DELETE FROM "RolePermissions" WHERE '
                '"RoleId" = (SELECT "Id" FROM "Roles" WHERE "Code" = :code) AND '
                '"PermissionId" = (SELECT "Id" FROM "Permissions" WHERE "Module" = :m AND "Action" = \'IMPORT\')'
            ),
            {"code": role_code, "m": module},
        )
