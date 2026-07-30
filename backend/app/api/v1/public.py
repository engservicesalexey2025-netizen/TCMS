from sqlalchemy import select

from fastapi import APIRouter

from app.api.deps import DbSession
from app.models.org import OrgUnit
from app.models.project import Project
from app.models.user import Role
from app.schemas.org import OrgUnitOut
from app.schemas.public import ProjectLookupOut, RoleLookupOut

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/roles", response_model=list[RoleLookupOut])
def list_roles(db: DbSession):
    """Публичный справочник ролей — нужен форме заявки на доступ, у
    заявителя ещё нет токена (см. access_requests.py).
    """
    return db.scalars(select(Role).where(Role.IsActive.is_(True))).all()


@router.get("/org-units", response_model=list[OrgUnitOut])
def list_org_units_public(db: DbSession):
    return db.scalars(select(OrgUnit).where(OrgUnit.IsActive.is_(True))).all()


@router.get("/projects", response_model=list[ProjectLookupOut])
def list_projects_public(db: DbSession):
    """Публичный справочник проектов — форма заявки на доступ позволяет
    указать проект, на который запрашивается доступ (§4 ТЗ)."""
    return db.scalars(select(Project).where(Project.IsActive.is_(True))).all()
