from app.api.v1.crud_router import build_crud_router
from app.models.contractor import Contractor
from app.models.enums import RoleCode
from app.schemas.contractor import ContractorCreate, ContractorOut, ContractorUpdate

router = build_crud_router(
    model=Contractor,
    create_schema=ContractorCreate,
    update_schema=ContractorUpdate,
    out_schema=ContractorOut,
    prefix="/contractors",
    tags=["contractors"],
    search_fields=["Name"],
    write_roles=(RoleCode.ADMIN, RoleCode.DEPARTMENT_HEAD),
)
