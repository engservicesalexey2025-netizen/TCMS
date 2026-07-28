import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import RoleCode
from app.models.org import OrgUnit
from app.models.user import User, UserOrgAccess

UNRESTRICTED_ROLES = {RoleCode.ADMIN, RoleCode.DIVISION_DIRECTOR}
READ_ONLY_ROLES = {RoleCode.DIVISION_DIRECTOR, RoleCode.OBSERVER}


def get_accessible_org_unit_ids(db: Session, user: User) -> set[uuid.UUID] | None:
    """Returns the set of OrgUnit ids the user may operate on, including all
    descendants of units they are directly assigned to. `None` means
    unrestricted (Admin / DivisionDirector — Тома 1А §2, роль важнее записи
    в join-таблице).
    """
    role_code = user.Role.Code
    if role_code in UNRESTRICTED_ROLES:
        return None

    direct_ids = set(
        db.scalars(
            select(UserOrgAccess.OrgUnitId).where(UserOrgAccess.UserId == user.Id)
        ).all()
    )
    if not direct_ids:
        return set()

    all_units = db.scalars(select(OrgUnit)).all()
    children_by_parent: dict[uuid.UUID | None, list[uuid.UUID]] = {}
    for unit in all_units:
        children_by_parent.setdefault(unit.ParentOrgUnitId, []).append(unit.Id)

    accessible = set(direct_ids)
    frontier = list(direct_ids)
    while frontier:
        current = frontier.pop()
        for child_id in children_by_parent.get(current, []):
            if child_id not in accessible:
                accessible.add(child_id)
                frontier.append(child_id)
    return accessible


def can_write(user: User) -> bool:
    return user.Role.Code not in READ_ONLY_ROLES
