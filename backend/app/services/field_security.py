"""Column-Level Security (§14 ТЗ): обобщение прежнего одноразового
FULL_PII_ROLES/masking.py на любую сущность и любое поле, управляемое через
таблицу ColumnPermissions вместо хардкода в коде.
"""
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import ColumnPermission
from app.models.user import User
from app.services.masking import mask_iin

# Реестр функций частичного маскирования по имени поля — режим 'MASKED'
# берёт функцию отсюда; для новых полей достаточно дописать сюда одну строку.
MASK_FUNCTIONS = {
    "IIN": mask_iin,
}

_MODE_RANK = {"HIDDEN": 0, "MASKED": 1, "FULL": 2}


def get_field_modes(db: Session, entity_name: str, user: User) -> dict[str, str]:
    """Возвращает {FieldName: Mode} для всех полей entity_name, у которых
    есть хоть одна строка ColumnPermissions, применимая к этому пользователю
    (по любой из его активных ролей — берётся наименее строгий режим среди
    них — или персонально). Поля без строк не попадают в словарь: вызывающий
    код должен трактовать отсутствие ключа как режим FULL (сегодняшнее
    поведение по умолчанию)."""
    from app.services.permissions import get_active_role_ids

    role_ids = get_active_role_ids(db, user)

    rows = db.scalars(
        select(ColumnPermission).where(ColumnPermission.EntityName == entity_name)
    ).all()

    modes: dict[str, str] = {}
    for row in rows:
        if row.RoleId is not None and row.RoleId in role_ids:
            current = modes.get(row.FieldName)
            if current is None or _MODE_RANK[row.Mode] > _MODE_RANK[current]:
                modes[row.FieldName] = row.Mode

    # Персональное правило всегда побеждает ролевое, в любую сторону.
    for row in rows:
        if row.UserId is not None and row.UserId == user.Id:
            modes[row.FieldName] = row.Mode

    return modes


def apply(entity_name: str, record: dict[str, Any], user: User, db: Session) -> dict[str, Any]:
    """Прогоняет словарь полей сущности через колоночную безопасность:
    убирает ключ при HIDDEN, маскирует при MASKED, оставляет как есть иначе."""
    modes = get_field_modes(db, entity_name, user)
    if not modes:
        return record

    result = dict(record)
    for field_name, mode in modes.items():
        if field_name not in result:
            continue
        if mode == "HIDDEN":
            result.pop(field_name, None)
        elif mode == "MASKED":
            mask_fn = MASK_FUNCTIONS.get(field_name)
            result[field_name] = mask_fn(result[field_name]) if mask_fn else result[field_name]
    return result
