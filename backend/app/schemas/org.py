import uuid

from pydantic import BaseModel

from app.models.enums import OrgUnitType
from app.schemas.common import AuditFields


class OrgUnitCreate(BaseModel):
    Name: str
    UnitType: OrgUnitType
    ParentOrgUnitId: uuid.UUID | None = None
    Comment: str | None = None


class OrgUnitUpdate(BaseModel):
    Name: str | None = None
    ParentOrgUnitId: uuid.UUID | None = None
    Comment: str | None = None


class OrgUnitOut(AuditFields):
    Name: str
    UnitType: OrgUnitType
    ParentOrgUnitId: uuid.UUID | None


class PositionCreate(BaseModel):
    Name: str
    Comment: str | None = None


class PositionOut(AuditFields):
    Name: str


class CityCreate(BaseModel):
    Name: str
    Comment: str | None = None


class CityOut(AuditFields):
    Name: str


class LegalEntityCreate(BaseModel):
    Name: str
    Comment: str | None = None


class LegalEntityOut(AuditFields):
    Name: str
