"""Разовая инициализация: 5 ролей системы + права + первый Admin-пользователь.

Запуск: python -m app.seed
Без этого некому одобрять заявки на доступ (курица и яйцо).

Права (RolePermissions/ColumnPermissions/BypassDataScope) сеются здесь, а не
только в Alembic-миграциях: несколько ранних RBAC-миграций сеяли эти данные
через UPDATE/INSERT, завязанные на существование строк Roles по Code — это
корректно только если Roles уже существуют на момент миграции (так было в
локальной разработке, где Roles появились до RBAC-модуля). На свежей базе
`alembic upgrade head` выполняется раньше `app.seed` (см. start.sh), поэтому
Roles ещё не существует, и те миграции молча не находят строк для
обновления/вставки. Здесь та же сеющая логика сделана независимой от
порядка: выполняется после создания Roles и безопасна при повторных запусках
(добавляет только отсутствующее).
"""
import os

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.enums import RoleCode
from app.models.permission import ColumnPermission, Permission, RolePermission, UserRole
from app.models.user import Role, User

ROLE_NAMES = {
    RoleCode.ADMIN: "Администратор",
    RoleCode.DIVISION_DIRECTOR: "Директор Дивизиона",
    RoleCode.DEPARTMENT_HEAD: "Руководитель Управления",
    RoleCode.GROUP_HEAD: "Руководитель Группы",
    RoleCode.OBSERVER: "Наблюдатель",
}

BYPASS_DATA_SCOPE_ROLES = {RoleCode.ADMIN, RoleCode.DIVISION_DIRECTOR}

# (Module, Action) пары на роль — точный снимок рабочей конфигурации прав.
ROLE_PERMISSIONS: dict[RoleCode, list[tuple[str, str]]] = {
    RoleCode.ADMIN: [
        ("ACCESS_REQUESTS", "CREATE"), ("ACCESS_REQUESTS", "DELETE"), ("ACCESS_REQUESTS", "IMPORT"),
        ("ACCESS_REQUESTS", "UPDATE"), ("ACCESS_REQUESTS", "VIEW"),
        ("ASSIGNMENTS", "CREATE"), ("ASSIGNMENTS", "DELETE"), ("ASSIGNMENTS", "IMPORT"),
        ("ASSIGNMENTS", "UPDATE"), ("ASSIGNMENTS", "VIEW"),
        ("ASSIGNMENT_ROLES", "CREATE"), ("ASSIGNMENT_ROLES", "DELETE"), ("ASSIGNMENT_ROLES", "IMPORT"),
        ("ASSIGNMENT_ROLES", "UPDATE"), ("ASSIGNMENT_ROLES", "VIEW"),
        ("CERTIFICATION_LEVELS", "CREATE"), ("CERTIFICATION_LEVELS", "DELETE"), ("CERTIFICATION_LEVELS", "IMPORT"),
        ("CERTIFICATION_LEVELS", "UPDATE"), ("CERTIFICATION_LEVELS", "VIEW"),
        ("CITIES", "CREATE"), ("CITIES", "DELETE"), ("CITIES", "IMPORT"), ("CITIES", "UPDATE"), ("CITIES", "VIEW"),
        ("CONTOURS", "CREATE"), ("CONTOURS", "DELETE"), ("CONTOURS", "IMPORT"), ("CONTOURS", "UPDATE"), ("CONTOURS", "VIEW"),
        ("CONTRACTORS", "CREATE"), ("CONTRACTORS", "DELETE"), ("CONTRACTORS", "IMPORT"),
        ("CONTRACTORS", "UPDATE"), ("CONTRACTORS", "VIEW"),
        ("CONTROL_SYSTEMS", "CREATE"), ("CONTROL_SYSTEMS", "DELETE"), ("CONTROL_SYSTEMS", "IMPORT"),
        ("CONTROL_SYSTEMS", "UPDATE"), ("CONTROL_SYSTEMS", "VIEW"),
        ("DELEGATION", "CREATE"),
        ("EMPLOYEES", "CREATE"), ("EMPLOYEES", "DELETE"), ("EMPLOYEES", "EXPORT"), ("EMPLOYEES", "IMPORT"),
        ("EMPLOYEES", "UPDATE"), ("EMPLOYEES", "VIEW"),
        ("EMPLOYEE_CERTIFICATES", "CREATE"), ("EMPLOYEE_CERTIFICATES", "DELETE"), ("EMPLOYEE_CERTIFICATES", "IMPORT"),
        ("EMPLOYEE_CERTIFICATES", "UPDATE"), ("EMPLOYEE_CERTIFICATES", "VIEW"),
        ("KPI", "CREATE"), ("KPI", "DELETE"), ("KPI", "IMPORT"), ("KPI", "UPDATE"), ("KPI", "VIEW"),
        ("KPI_SETTINGS", "UPDATE"), ("KPI_SETTINGS", "VIEW"),
        ("LEGAL_ENTITIES", "CREATE"), ("LEGAL_ENTITIES", "DELETE"), ("LEGAL_ENTITIES", "IMPORT"),
        ("LEGAL_ENTITIES", "UPDATE"), ("LEGAL_ENTITIES", "VIEW"),
        ("OBJECTS", "CREATE"), ("OBJECTS", "DELETE"), ("OBJECTS", "IMPORT"), ("OBJECTS", "UPDATE"), ("OBJECTS", "VIEW"),
        ("ORG_UNITS", "CREATE"), ("ORG_UNITS", "DELETE"), ("ORG_UNITS", "IMPORT"), ("ORG_UNITS", "UPDATE"), ("ORG_UNITS", "VIEW"),
        ("POSITIONS", "CREATE"), ("POSITIONS", "DELETE"), ("POSITIONS", "IMPORT"), ("POSITIONS", "UPDATE"), ("POSITIONS", "VIEW"),
        ("PROJECTS", "CREATE"), ("PROJECTS", "DELETE"), ("PROJECTS", "EXPORT"), ("PROJECTS", "IMPORT"),
        ("PROJECTS", "UPDATE"), ("PROJECTS", "VIEW"),
        ("PROJECT_DOCUMENTS", "CREATE"), ("PROJECT_DOCUMENTS", "DELETE"), ("PROJECT_DOCUMENTS", "IMPORT"),
        ("PROJECT_DOCUMENTS", "UPDATE"), ("PROJECT_DOCUMENTS", "VIEW"),
        ("PROJECT_STAGES", "CREATE"), ("PROJECT_STAGES", "DELETE"), ("PROJECT_STAGES", "IMPORT"),
        ("PROJECT_STAGES", "UPDATE"), ("PROJECT_STAGES", "VIEW"),
        ("PROJECT_TYPES", "CREATE"), ("PROJECT_TYPES", "DELETE"), ("PROJECT_TYPES", "IMPORT"),
        ("PROJECT_TYPES", "UPDATE"), ("PROJECT_TYPES", "VIEW"),
        ("REMARKS", "CREATE"), ("REMARKS", "DELETE"), ("REMARKS", "IMPORT"), ("REMARKS", "UPDATE"), ("REMARKS", "VIEW"),
        ("ROLES", "CREATE"), ("ROLES", "DELETE"), ("ROLES", "IMPORT"), ("ROLES", "MANAGE"),
        ("ROLES", "UPDATE"), ("ROLES", "VIEW"),
        ("SECURITY_LOG", "VIEW"),
        ("USERS", "CREATE"), ("USERS", "DELETE"), ("USERS", "UPDATE"), ("USERS", "VIEW"), ("USERS", "VIEW_AS"),
        ("WORKLOAD_NORMS", "CREATE"), ("WORKLOAD_NORMS", "DELETE"), ("WORKLOAD_NORMS", "IMPORT"),
        ("WORKLOAD_NORMS", "UPDATE"), ("WORKLOAD_NORMS", "VIEW"),
    ],
    RoleCode.DIVISION_DIRECTOR: [
        ("ACCESS_REQUESTS", "CREATE"), ("ACCESS_REQUESTS", "DELETE"), ("ACCESS_REQUESTS", "EXPORT"),
        ("ACCESS_REQUESTS", "IMPORT"), ("ACCESS_REQUESTS", "UPDATE"), ("ACCESS_REQUESTS", "VIEW"),
        ("ASSIGNMENTS", "VIEW"), ("ASSIGNMENT_ROLES", "VIEW"),
        ("CERTIFICATION_LEVELS", "VIEW"), ("CITIES", "VIEW"), ("CONTOURS", "VIEW"), ("CONTRACTORS", "VIEW"),
        ("CONTROL_SYSTEMS", "VIEW"),
        ("EMPLOYEES", "VIEW"), ("EMPLOYEE_CERTIFICATES", "VIEW"),
        ("KPI", "VIEW"), ("KPI_SETTINGS", "VIEW"), ("LEGAL_ENTITIES", "VIEW"), ("OBJECTS", "VIEW"),
        ("ORG_UNITS", "VIEW"), ("POSITIONS", "VIEW"),
        ("PROJECTS", "VIEW"), ("PROJECT_DOCUMENTS", "VIEW"), ("PROJECT_STAGES", "VIEW"), ("PROJECT_TYPES", "VIEW"),
    ],
    RoleCode.DEPARTMENT_HEAD: [
        ("ACCESS_REQUESTS", "VIEW"),
        ("ASSIGNMENTS", "CREATE"), ("ASSIGNMENTS", "DELETE"), ("ASSIGNMENTS", "UPDATE"), ("ASSIGNMENTS", "VIEW"),
        ("ASSIGNMENT_ROLES", "CREATE"), ("ASSIGNMENT_ROLES", "DELETE"), ("ASSIGNMENT_ROLES", "UPDATE"),
        ("ASSIGNMENT_ROLES", "VIEW"),
        ("CERTIFICATION_LEVELS", "VIEW"), ("CITIES", "VIEW"), ("CONTOURS", "VIEW"),
        ("CONTRACTORS", "CREATE"), ("CONTRACTORS", "DELETE"), ("CONTRACTORS", "UPDATE"), ("CONTRACTORS", "VIEW"),
        ("CONTROL_SYSTEMS", "VIEW"),
        ("DELEGATION", "CREATE"),
        ("EMPLOYEES", "CREATE"), ("EMPLOYEES", "DELETE"), ("EMPLOYEES", "IMPORT"),
        ("EMPLOYEES", "UPDATE"), ("EMPLOYEES", "VIEW"),
        ("EMPLOYEE_CERTIFICATES", "CREATE"), ("EMPLOYEE_CERTIFICATES", "DELETE"), ("EMPLOYEE_CERTIFICATES", "UPDATE"),
        ("EMPLOYEE_CERTIFICATES", "VIEW"),
        ("KPI", "CREATE"), ("KPI", "DELETE"), ("KPI", "UPDATE"), ("KPI", "VIEW"), ("KPI_SETTINGS", "VIEW"),
        ("LEGAL_ENTITIES", "VIEW"),
        ("OBJECTS", "CREATE"), ("OBJECTS", "DELETE"), ("OBJECTS", "UPDATE"), ("OBJECTS", "VIEW"),
        ("ORG_UNITS", "VIEW"), ("POSITIONS", "VIEW"),
        ("PROJECTS", "CREATE"), ("PROJECTS", "DELETE"), ("PROJECTS", "IMPORT"), ("PROJECTS", "UPDATE"), ("PROJECTS", "VIEW"),
        ("PROJECT_DOCUMENTS", "CREATE"), ("PROJECT_DOCUMENTS", "DELETE"), ("PROJECT_DOCUMENTS", "UPDATE"),
        ("PROJECT_DOCUMENTS", "VIEW"),
        ("PROJECT_STAGES", "VIEW"), ("PROJECT_TYPES", "VIEW"),
        ("REMARKS", "CREATE"), ("REMARKS", "DELETE"), ("REMARKS", "UPDATE"), ("REMARKS", "VIEW"),
        ("ROLES", "VIEW"),
        ("WORKLOAD_NORMS", "CREATE"), ("WORKLOAD_NORMS", "DELETE"), ("WORKLOAD_NORMS", "UPDATE"), ("WORKLOAD_NORMS", "VIEW"),
    ],
    RoleCode.GROUP_HEAD: [
        ("ACCESS_REQUESTS", "VIEW"),
        ("ASSIGNMENTS", "CREATE"), ("ASSIGNMENTS", "DELETE"), ("ASSIGNMENTS", "UPDATE"), ("ASSIGNMENTS", "VIEW"),
        ("ASSIGNMENT_ROLES", "CREATE"), ("ASSIGNMENT_ROLES", "DELETE"), ("ASSIGNMENT_ROLES", "UPDATE"),
        ("ASSIGNMENT_ROLES", "VIEW"),
        ("CERTIFICATION_LEVELS", "VIEW"), ("CITIES", "VIEW"), ("CONTOURS", "VIEW"), ("CONTRACTORS", "VIEW"),
        ("CONTROL_SYSTEMS", "VIEW"),
        ("DELEGATION", "CREATE"),
        ("EMPLOYEES", "CREATE"), ("EMPLOYEES", "DELETE"), ("EMPLOYEES", "IMPORT"),
        ("EMPLOYEES", "UPDATE"), ("EMPLOYEES", "VIEW"),
        ("EMPLOYEE_CERTIFICATES", "CREATE"), ("EMPLOYEE_CERTIFICATES", "DELETE"), ("EMPLOYEE_CERTIFICATES", "UPDATE"),
        ("EMPLOYEE_CERTIFICATES", "VIEW"),
        ("KPI", "VIEW"), ("KPI_SETTINGS", "VIEW"), ("LEGAL_ENTITIES", "VIEW"),
        ("OBJECTS", "CREATE"), ("OBJECTS", "DELETE"), ("OBJECTS", "UPDATE"), ("OBJECTS", "VIEW"),
        ("ORG_UNITS", "VIEW"), ("POSITIONS", "VIEW"),
        ("PROJECTS", "VIEW"), ("PROJECT_DOCUMENTS", "VIEW"), ("PROJECT_STAGES", "VIEW"), ("PROJECT_TYPES", "VIEW"),
        ("REMARKS", "CREATE"), ("REMARKS", "DELETE"), ("REMARKS", "UPDATE"), ("REMARKS", "VIEW"),
        ("ROLES", "VIEW"),
        ("WORKLOAD_NORMS", "VIEW"),
    ],
    RoleCode.OBSERVER: [
        ("ACCESS_REQUESTS", "VIEW"), ("ASSIGNMENTS", "VIEW"), ("ASSIGNMENT_ROLES", "VIEW"),
        ("CERTIFICATION_LEVELS", "VIEW"), ("CITIES", "VIEW"), ("CONTOURS", "VIEW"), ("CONTRACTORS", "VIEW"),
        ("CONTROL_SYSTEMS", "VIEW"),
        ("EMPLOYEES", "VIEW"), ("EMPLOYEE_CERTIFICATES", "VIEW"),
        ("KPI", "VIEW"), ("KPI_SETTINGS", "VIEW"), ("LEGAL_ENTITIES", "VIEW"), ("OBJECTS", "VIEW"),
    ],
}

# (RoleCode, EntityName, FieldName, Mode) — маскирование чувствительных полей.
COLUMN_PERMISSIONS: list[tuple[RoleCode, str, str, str]] = [
    (RoleCode.DIVISION_DIRECTOR, "Employees", "IIN", "MASKED"),
    (RoleCode.DIVISION_DIRECTOR, "Employees", "PersonalPhone", "HIDDEN"),
    (RoleCode.OBSERVER, "Employees", "PersonalPhone", "HIDDEN"),
    (RoleCode.OBSERVER, "Employees", "IIN", "MASKED"),
    (RoleCode.OBSERVER, "Employees", "BirthDate", "MASKED"),
]


def _seed_role_permissions(db, roles_by_code: dict[RoleCode, Role]) -> None:
    permission_by_key = {
        (p.Module, p.Action): p
        for p in db.scalars(select(Permission))
    }
    existing_pairs = {
        (rp.RoleId, rp.PermissionId) for rp in db.scalars(select(RolePermission))
    }
    added = 0
    for role_code, pairs in ROLE_PERMISSIONS.items():
        role = roles_by_code[role_code]
        for module, action in pairs:
            permission = permission_by_key.get((module, action))
            if permission is None:
                continue
            if (role.Id, permission.Id) in existing_pairs:
                continue
            db.add(RolePermission(RoleId=role.Id, PermissionId=permission.Id))
            existing_pairs.add((role.Id, permission.Id))
            added += 1
    if added:
        print(f"Добавлено прав ролям (RolePermissions): {added}")


def _seed_column_permissions(db, roles_by_code: dict[RoleCode, Role]) -> None:
    existing = {
        (cp.RoleId, cp.EntityName, cp.FieldName)
        for cp in db.scalars(select(ColumnPermission))
        if cp.RoleId is not None
    }
    added = 0
    for role_code, entity, field, mode in COLUMN_PERMISSIONS:
        role = roles_by_code[role_code]
        if (role.Id, entity, field) in existing:
            continue
        db.add(ColumnPermission(RoleId=role.Id, EntityName=entity, FieldName=field, Mode=mode))
        existing.add((role.Id, entity, field))
        added += 1
    if added:
        print(f"Добавлено скрытий/масок полей (ColumnPermissions): {added}")


def seed() -> None:
    db = SessionLocal()
    try:
        roles_by_code: dict[RoleCode, Role] = {}
        for code, name in ROLE_NAMES.items():
            role = db.scalar(select(Role).where(Role.Code == code))
            if role is None:
                role = Role(Code=code, Name=name)
                db.add(role)
                db.flush()
                print(f"Создана роль: {name} ({code.value})")
            should_bypass = code in BYPASS_DATA_SCOPE_ROLES
            if role.BypassDataScope != should_bypass:
                role.BypassDataScope = should_bypass
            roles_by_code[code] = role
        db.flush()

        _seed_role_permissions(db, roles_by_code)
        _seed_column_permissions(db, roles_by_code)

        admin_login = os.environ.get("SEED_ADMIN_LOGIN", "admin")
        if not db.scalar(select(User).where(User.Login == admin_login)):
            admin_password = os.environ.get("SEED_ADMIN_PASSWORD", "ChangeMe123!")
            admin = User(
                Login=admin_login,
                Email=os.environ.get("SEED_ADMIN_EMAIL", "admin@tcms.local"),
                HashedPassword=hash_password(admin_password),
            )
            db.add(admin)
            db.flush()
            admin.CreatedBy = admin.Id
            admin.ModifiedBy = admin.Id
            db.add(
                UserRole(
                    UserId=admin.Id,
                    RoleId=roles_by_code[RoleCode.ADMIN].Id,
                    CreatedBy=admin.Id,
                    ModifiedBy=admin.Id,
                )
            )
            print(
                f"Создан администратор: логин='{admin_login}', "
                f"пароль='{admin_password}' — смените после первого входа."
            )
        else:
            print(f"Администратор '{admin_login}' уже существует, пропускаю.")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
