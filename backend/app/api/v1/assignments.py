from app.api.v1.crud_router import build_crud_router
from app.models.assignment import Assignment
from app.models.enums import RoleCode
from app.schemas.assignment import AssignmentCreate, AssignmentOut, AssignmentUpdate

router = build_crud_router(
    model=Assignment,
    create_schema=AssignmentCreate,
    update_schema=AssignmentUpdate,
    out_schema=AssignmentOut,
    prefix="/assignments",
    tags=["assignments"],
    write_roles=(RoleCode.ADMIN, RoleCode.DEPARTMENT_HEAD, RoleCode.GROUP_HEAD),
)
