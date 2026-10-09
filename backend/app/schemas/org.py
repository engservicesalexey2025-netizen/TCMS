import uuid

from pydantic import BaseModel

from app.models.enums import OrgUnitType
from app.schemas.common import AuditFields


class OrgUnitCreate(BaseModel):
    Name: str
    UnitType: OrgUnitType
    Code: str | None = None
    ParentOrgUnitId: uuid.UUID | None = None
    Comment: str | None = None


class OrgUnitUpdate(BaseModel):
    Name: str | None = None
    UnitType: OrgUnitType | None = None
    Code: str | None = None
    ParentOrgUnitId: uuid.UUID | None = None
    Comment: str | None = None


class OrgUnitOut(AuditFields):
    Name: str
    UnitType: OrgUnitType
    Code: str | None
    ParentOrgUnitId: uuid.UUID | None
    ManagerEmployeeId: uuid.UUID | None


class OrgUnitTreeItem(BaseModel):
    Id: uuid.UUID
    Name: str
    UnitType: OrgUnitType
    ParentOrgUnitId: uuid.UUID | None
    IsActive: bool
    EmployeeCount: int


class OrgUnitEmployeeItem(BaseModel):
    Id: uuid.UUID
    FullName: str
    PositionName: str | None
    Status: str


class OrgUnitChildItem(BaseModel):
    Id: uuid.UUID
    Name: str
    UnitType: OrgUnitType


class OrgUnitDetail(OrgUnitOut):
    ManagerName: str | None
    ParentName: str | None
    Children: list[OrgUnitChildItem]
    Employees: list[OrgUnitEmployeeItem]


class OrgUnitFullTreeItem(BaseModel):
    """Полностью развёрнутый узел для наглядного списка «кто за кем идёт»
    (реестр без табличного дерева-с-подразделениями) — один запрос вместо
    N обращений к /detail на каждый узел."""

    Id: uuid.UUID
    Name: str
    UnitType: OrgUnitType
    ManagerName: str | None
    Employees: list[OrgUnitEmployeeItem]
    Children: list["OrgUnitFullTreeItem"]


OrgUnitFullTreeItem.model_rebuild()


class AssignEmployeeRequest(BaseModel):
    EmployeeId: uuid.UUID


class SetManagerRequest(BaseModel):
    EmployeeId: uuid.UUID | None = None
    Force: bool = False


class ImportSpecialistsRowError(BaseModel):
    RowNumber: int
    Message: str


class ImportSpecialistsResult(BaseModel):
    Assigned: int
    Unchanged: int
    Failed: int
    Errors: list[ImportSpecialistsRowError]


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
