from app.api.v1.crud_router import build_crud_router
from app.models.remark import Remark
from app.schemas.remark import RemarkCreate, RemarkOut, RemarkUpdate

# RLS по подрядчику (§15 ТЗ: "подрядчик видит только собственные замечания")
# сознательно не подключается здесь: сегодня нет способа связать User с
# Contractor (модель User привязывается только к Employee) — это отдельная
# задача идентификации подрядчика-пользователя, не часть этого захода.
router = build_crud_router(
    model=Remark,
    create_schema=RemarkCreate,
    update_schema=RemarkUpdate,
    out_schema=RemarkOut,
    prefix="/remarks",
    tags=["remarks"],
    search_fields=["Title", "Description"],
    module="REMARKS",
)
