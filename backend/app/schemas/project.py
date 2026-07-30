import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import AuditAction, ProjectStatus
from app.schemas.common import AuditFields


class ProjectTypeCreate(BaseModel):
    Name: str
    Comment: str | None = None


class ProjectTypeOut(AuditFields):
    Name: str


class ProjectStageCreate(BaseModel):
    Name: str
    Comment: str | None = None


class ProjectStageOut(AuditFields):
    Name: str


class ContourCreate(BaseModel):
    Name: str
    Comment: str | None = None


class ContourOut(AuditFields):
    Name: str


class ControlSystemCreate(BaseModel):
    Name: str
    Comment: str | None = None


class ControlSystemOut(AuditFields):
    Name: str


class ProjectCreate(BaseModel):
    Name: str
    CityId: uuid.UUID | None = None
    Address: str | None = None
    Description: str | None = None
    OrgUnitId: uuid.UUID | None = None
    ProjectTypeId: uuid.UUID | None = None
    ProjectStageId: uuid.UUID | None = None
    ContourId: uuid.UUID | None = None
    ControlSystemId: uuid.UUID | None = None
    Status: ProjectStatus = ProjectStatus.IN_PROGRESS
    DeveloperId: uuid.UUID | None = None
    ContractorId: uuid.UUID | None = None
    GeneralContractorId: uuid.UUID | None = None
    SubcontractorId: uuid.UUID | None = None
    ContractNumber: str | None = None
    Area: float | None = None
    Cost: float | None = None
    GisLink: str | None = None
    GaskTicketNumber: str | None = None
    GaskNotificationNumber: str | None = None
    GaskTicketDate: date | None = None
    GaskTicketExpiryDate: date | None = None
    ActualEndDate: date | None = None
    Comment: str | None = None


class ProjectUpdate(BaseModel):
    Name: str | None = None
    CityId: uuid.UUID | None = None
    Address: str | None = None
    Description: str | None = None
    OrgUnitId: uuid.UUID | None = None
    ProjectTypeId: uuid.UUID | None = None
    ProjectStageId: uuid.UUID | None = None
    ContourId: uuid.UUID | None = None
    ControlSystemId: uuid.UUID | None = None
    Status: ProjectStatus | None = None
    DeveloperId: uuid.UUID | None = None
    ContractorId: uuid.UUID | None = None
    GeneralContractorId: uuid.UUID | None = None
    SubcontractorId: uuid.UUID | None = None
    ContractNumber: str | None = None
    Area: float | None = None
    Cost: float | None = None
    GisLink: str | None = None
    GaskTicketNumber: str | None = None
    GaskNotificationNumber: str | None = None
    GaskTicketDate: date | None = None
    GaskTicketExpiryDate: date | None = None
    ActualEndDate: date | None = None
    Comment: str | None = None


class ProjectOut(AuditFields):
    Name: str
    CityId: uuid.UUID | None
    Address: str | None
    Description: str | None
    OrgUnitId: uuid.UUID | None
    ProjectTypeId: uuid.UUID | None
    ProjectStageId: uuid.UUID | None
    ContourId: uuid.UUID | None
    ControlSystemId: uuid.UUID | None
    Status: ProjectStatus
    DeveloperId: uuid.UUID | None
    ContractorId: uuid.UUID | None
    GeneralContractorId: uuid.UUID | None
    SubcontractorId: uuid.UUID | None
    ContractNumber: str | None
    Area: float | None
    Cost: float | None
    GisLink: str | None
    GaskTicketNumber: str | None
    GaskNotificationNumber: str | None
    GaskTicketDate: date | None
    GaskTicketExpiryDate: date | None
    ActualEndDate: date | None


class ProjectHistoryEntryOut(BaseModel):
    Id: uuid.UUID
    Action: AuditAction
    ChangedByUserId: uuid.UUID | None
    ChangedByLogin: str | None
    ChangedDate: datetime
    FieldName: str | None
    OldValue: str | None
    NewValue: str | None


class ConstructionObjectCreate(BaseModel):
    ProjectId: uuid.UUID
    Name: str
    Address: str | None = None
    Comment: str | None = None


class ConstructionObjectUpdate(BaseModel):
    Name: str | None = None
    Address: str | None = None
    Comment: str | None = None


class ConstructionObjectOut(AuditFields):
    ProjectId: uuid.UUID
    Name: str
    Address: str | None
