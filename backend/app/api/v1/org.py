from app.api.v1.crud_router import build_crud_router
from app.models.enums import RoleCode
from app.models.org import City, LegalEntity, OrgUnit, Position
from app.schemas.org import (
    CityCreate,
    CityOut,
    LegalEntityCreate,
    LegalEntityOut,
    OrgUnitCreate,
    OrgUnitOut,
    OrgUnitUpdate,
    PositionCreate,
    PositionOut,
)

org_units_router = build_crud_router(
    model=OrgUnit,
    create_schema=OrgUnitCreate,
    update_schema=OrgUnitUpdate,
    out_schema=OrgUnitOut,
    prefix="/org-units",
    tags=["org-units"],
    search_fields=["Name"],
    write_roles=(RoleCode.ADMIN,),
)

positions_router = build_crud_router(
    model=Position,
    create_schema=PositionCreate,
    update_schema=PositionCreate,
    out_schema=PositionOut,
    prefix="/positions",
    tags=["positions"],
    search_fields=["Name"],
    write_roles=(RoleCode.ADMIN,),
)

cities_router = build_crud_router(
    model=City,
    create_schema=CityCreate,
    update_schema=CityCreate,
    out_schema=CityOut,
    prefix="/cities",
    tags=["cities"],
    search_fields=["Name"],
    write_roles=(RoleCode.ADMIN,),
)

legal_entities_router = build_crud_router(
    model=LegalEntity,
    create_schema=LegalEntityCreate,
    update_schema=LegalEntityCreate,
    out_schema=LegalEntityOut,
    prefix="/legal-entities",
    tags=["legal-entities"],
    search_fields=["Name"],
    write_roles=(RoleCode.ADMIN,),
)
