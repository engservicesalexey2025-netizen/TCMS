from app.api.v1.crud_router import build_crud_router
from app.models.enums import RoleCode
from app.models.project import ConstructionObject, Project
from app.schemas.project import (
    ConstructionObjectCreate,
    ConstructionObjectOut,
    ConstructionObjectUpdate,
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
)

projects_router = build_crud_router(
    model=Project,
    create_schema=ProjectCreate,
    update_schema=ProjectUpdate,
    out_schema=ProjectOut,
    prefix="/projects",
    tags=["projects"],
    search_fields=["Name"],
    write_roles=(RoleCode.ADMIN, RoleCode.DEPARTMENT_HEAD),
)

objects_router = build_crud_router(
    model=ConstructionObject,
    create_schema=ConstructionObjectCreate,
    update_schema=ConstructionObjectUpdate,
    out_schema=ConstructionObjectOut,
    prefix="/objects",
    tags=["objects"],
    search_fields=["Name", "Address"],
    write_roles=(RoleCode.ADMIN, RoleCode.DEPARTMENT_HEAD, RoleCode.GROUP_HEAD),
)
