from app.api.v1.crud_router import build_crud_router
from app.models.enums import RoleCode
from app.models.remark import Remark
from app.schemas.remark import RemarkCreate, RemarkOut, RemarkUpdate

router = build_crud_router(
    model=Remark,
    create_schema=RemarkCreate,
    update_schema=RemarkUpdate,
    out_schema=RemarkOut,
    prefix="/remarks",
    tags=["remarks"],
    search_fields=["Title", "Description"],
    write_roles=(RoleCode.ADMIN, RoleCode.DEPARTMENT_HEAD, RoleCode.GROUP_HEAD),
)
