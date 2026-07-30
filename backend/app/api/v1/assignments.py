from app.api.v1.crud_router import build_crud_router
from app.models.assignment import Assignment, AssignmentRole
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentOut,
    AssignmentRoleCreate,
    AssignmentRoleOut,
    AssignmentUpdate,
)

router = build_crud_router(
    model=Assignment,
    create_schema=AssignmentCreate,
    update_schema=AssignmentUpdate,
    out_schema=AssignmentOut,
    prefix="/assignments",
    tags=["assignments"],
    module="ASSIGNMENTS",
    scoped=True,
)

assignment_roles_router = build_crud_router(
    model=AssignmentRole,
    create_schema=AssignmentRoleCreate,
    update_schema=AssignmentRoleCreate,
    out_schema=AssignmentRoleOut,
    prefix="/assignment-roles",
    tags=["assignment-roles"],
    search_fields=["Name"],
    module="ASSIGNMENT_ROLES",
)
