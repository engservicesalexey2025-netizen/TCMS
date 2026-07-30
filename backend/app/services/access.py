import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.org import OrgUnit
from app.models.user import Role, User, UserOrgAccess


def get_accessible_org_unit_ids(db: Session, user: User) -> set[uuid.UUID] | None:
    """Returns the set of OrgUnit ids the user may operate on, including all
    descendants of units they are directly assigned to. `None` means
    unrestricted — определяется данными (Roles.BypassDataScope), а не
    захардкоженным списком ролей (§15 ТЗ), и учитывает все активные роли
    пользователя (UserRoles), а не одну legacy Users.RoleId.
    """
    from app.services.permissions import get_active_role_ids

    role_ids = get_active_role_ids(db, user)
    if role_ids and db.scalar(
        select(Role.Id).where(Role.Id.in_(role_ids), Role.BypassDataScope.is_(True))
    ):
        return None

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    direct_rows = db.scalars(
        select(UserOrgAccess).where(
            UserOrgAccess.UserId == user.Id, UserOrgAccess.IsActive.is_(True)
        )
    ).all()
    # ExpiresAt=NULL — бессрочно; иначе временный доступ (§7 ТЗ) действует
    # только пока не истёк срок.
    direct_ids = {r.OrgUnitId for r in direct_rows if r.ExpiresAt is None or r.ExpiresAt > now}
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
