"""Разовая инициализация: 5 ролей системы + первый Admin-пользователь.

Запуск: python -m app.seed
Без этого некому одобрять заявки на доступ (курица и яйцо).
"""
import os

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.enums import RoleCode
from app.models.user import Role, User

ROLE_NAMES = {
    RoleCode.ADMIN: "Администратор",
    RoleCode.DIVISION_DIRECTOR: "Директор Дивизиона",
    RoleCode.DEPARTMENT_HEAD: "Руководитель Управления",
    RoleCode.GROUP_HEAD: "Руководитель Группы",
    RoleCode.OBSERVER: "Наблюдатель",
}


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
            roles_by_code[code] = role

        admin_login = os.environ.get("SEED_ADMIN_LOGIN", "admin")
        if not db.scalar(select(User).where(User.Login == admin_login)):
            admin_password = os.environ.get("SEED_ADMIN_PASSWORD", "ChangeMe123!")
            admin = User(
                Login=admin_login,
                Email=os.environ.get("SEED_ADMIN_EMAIL", "admin@tcms.local"),
                HashedPassword=hash_password(admin_password),
                RoleId=roles_by_code[RoleCode.ADMIN].Id,
            )
            db.add(admin)
            db.flush()
            admin.CreatedBy = admin.Id
            admin.ModifiedBy = admin.Id
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
