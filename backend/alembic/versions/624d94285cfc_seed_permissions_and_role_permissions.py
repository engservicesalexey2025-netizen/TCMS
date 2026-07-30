"""seed permissions and role permissions

Revision ID: 624d94285cfc
Revises: 6e1e2ae54a5c
Create Date: 2026-07-29 15:10:00.000000

Данные — литеральный слепок сегодняшних require_roles(...)/write_roles=(...)
гейтов, собранных по каждому роутеру на момент написания этой миграции (не
импортируется код приложения, чтобы миграция не зависела от будущих правок
роутеров). Цель: после перехода на require_permission() ни для одной из 5
существующих ролей не происходит регресса прав.
"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '624d94285cfc'
down_revision: Union[str, None] = '6e1e2ae54a5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


MODULES = [
    "ORG_UNITS", "POSITIONS", "CITIES", "LEGAL_ENTITIES", "EMPLOYEES",
    "EMPLOYEE_CERTIFICATES", "CERTIFICATION_LEVELS", "PROJECTS", "PROJECT_TYPES",
    "PROJECT_STAGES", "CONTOURS", "CONTROL_SYSTEMS", "OBJECTS", "PROJECT_DOCUMENTS",
    "CONTRACTORS", "ASSIGNMENTS", "ASSIGNMENT_ROLES", "REMARKS", "KPI",
    "WORKLOAD_NORMS", "ACCESS_REQUESTS", "ROLES",
]
ACTIONS = ["VIEW", "CREATE", "UPDATE", "DELETE", "IMPORT", "EXPORT"]

ACTION_NAMES = {
    "VIEW": "Просмотр", "CREATE": "Создание", "UPDATE": "Изменение",
    "DELETE": "Удаление", "IMPORT": "Импорт", "EXPORT": "Экспорт", "MANAGE": "Управление правами",
}

# Сегодняшние write_roles=(...)/require_roles(...) по каждому роутеру.
DEPARTMENT_HEAD_WRITE_MODULES = {
    "CONTRACTORS", "REMARKS", "EMPLOYEES", "ASSIGNMENTS", "ASSIGNMENT_ROLES",
    "PROJECTS", "OBJECTS", "KPI", "WORKLOAD_NORMS", "EMPLOYEE_CERTIFICATES",
    "PROJECT_DOCUMENTS",
}
GROUP_HEAD_WRITE_MODULES = {
    "REMARKS", "EMPLOYEES", "ASSIGNMENTS", "ASSIGNMENT_ROLES", "OBJECTS",
    "EMPLOYEE_CERTIFICATES",
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

    permission_ids: dict[tuple[str, str], uuid.UUID] = {}
    rows = []
    for module in MODULES:
        for action in ACTIONS:
            pid = uuid.uuid4()
            permission_ids[(module, action)] = pid
            rows.append({
                "Id": pid, "Module": module, "Action": action,
                "Code": f"{module}.{action}",
                "Name": f"{ACTION_NAMES[action]} — {module}",
                "IsActive": True, "Version": 1,
            })
    # Право на управление правами/ролями — отдельное действие, только у ROLES.
    manage_id = uuid.uuid4()
    permission_ids[("ROLES", "MANAGE")] = manage_id
    rows.append({
        "Id": manage_id, "Module": "ROLES", "Action": "MANAGE",
        "Code": "ROLES.MANAGE", "Name": ACTION_NAMES["MANAGE"],
        "IsActive": True, "Version": 1,
    })
    op.bulk_insert(permission_table, rows)

    role_ids = {
        code: bind.execute(
            sa.text('SELECT "Id" FROM "Roles" WHERE "Code" = :code'), {"code": code}
        ).scalar()
        for code in ("ADMIN", "DIVISION_DIRECTOR", "DEPARTMENT_HEAD", "GROUP_HEAD", "OBSERVER")
    }

    role_permission_table = sa.table(
        "RolePermissions",
        sa.column("Id", sa.UUID()),
        sa.column("RoleId", sa.UUID()),
        sa.column("PermissionId", sa.UUID()),
        sa.column("IsActive", sa.Boolean()),
        sa.column("Version", sa.Integer()),
    )

    grants: list[tuple[str, str, str]] = []  # (role_code, module, action)

    for role_code in role_ids:
        for module in MODULES:
            grants.append((role_code, module, "VIEW"))

    for module in MODULES:
        grants.append(("ADMIN", module, "CREATE"))
        grants.append(("ADMIN", module, "UPDATE"))
        grants.append(("ADMIN", module, "DELETE"))
        grants.append(("ADMIN", module, "IMPORT"))
    grants.append(("ADMIN", "EMPLOYEES", "EXPORT"))
    grants.append(("ADMIN", "ROLES", "MANAGE"))

    for module in DEPARTMENT_HEAD_WRITE_MODULES:
        grants.append(("DEPARTMENT_HEAD", module, "CREATE"))
        grants.append(("DEPARTMENT_HEAD", module, "UPDATE"))
        grants.append(("DEPARTMENT_HEAD", module, "DELETE"))

    for module in GROUP_HEAD_WRITE_MODULES:
        grants.append(("GROUP_HEAD", module, "CREATE"))
        grants.append(("GROUP_HEAD", module, "UPDATE"))
        grants.append(("GROUP_HEAD", module, "DELETE"))

    role_permission_rows = []
    seen = set()
    for role_code, module, action in grants:
        key = (role_code, module, action)
        if key in seen:
            continue
        seen.add(key)
        role_id = role_ids.get(role_code)
        permission_id = permission_ids.get((module, action))
        if role_id is None or permission_id is None:
            continue
        role_permission_rows.append({
            "Id": uuid.uuid4(), "RoleId": role_id, "PermissionId": permission_id,
            "IsActive": True, "Version": 1,
        })
    op.bulk_insert(role_permission_table, role_permission_rows)


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text('DELETE FROM "RolePermissions"'))
    bind.execute(sa.text('DELETE FROM "Permissions"'))
