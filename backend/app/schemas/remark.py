import uuid
from datetime import date

from pydantic import BaseModel

from app.models.enums import RemarkStatus
from app.schemas.common import AuditFields


class RemarkCreate(BaseModel):
    ObjectId: uuid.UUID
    ContractorId: uuid.UUID | None = None
    ResponsibleEmployeeId: uuid.UUID | None = None
    Title: str
    Description: str | None = None
    DueDate: date | None = None
    Comment: str | None = None


class RemarkUpdate(BaseModel):
    ContractorId: uuid.UUID | None = None
    ResponsibleEmployeeId: uuid.UUID | None = None
    Title: str | None = None
    Description: str | None = None
    Status: RemarkStatus | None = None
    DueDate: date | None = None
    ResolvedDate: date | None = None
    Comment: str | None = None


class RemarkOut(AuditFields):
    ObjectId: uuid.UUID
    ContractorId: uuid.UUID | None
    ResponsibleEmployeeId: uuid.UUID | None
    Title: str
    Description: str | None
    Status: RemarkStatus
    DueDate: date | None
    ResolvedDate: date | None
