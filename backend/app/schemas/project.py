import uuid
from datetime import date

from pydantic import BaseModel

from app.models.enums import ProjectStatus
from app.schemas.common import AuditFields


class ProjectCreate(BaseModel):
    Name: str
    OrgUnitId: uuid.UUID | None = None
    Area: float | None = None
    Cost: float | None = None
    StartDate: date | None = None
    EndDate: date | None = None
    Status: ProjectStatus = ProjectStatus.PLANNED
    Comment: str | None = None


class ProjectUpdate(BaseModel):
    Name: str | None = None
    OrgUnitId: uuid.UUID | None = None
    Area: float | None = None
    Cost: float | None = None
    StartDate: date | None = None
    EndDate: date | None = None
    Status: ProjectStatus | None = None
    Comment: str | None = None


class ProjectOut(AuditFields):
    Name: str
    OrgUnitId: uuid.UUID | None
    Area: float | None
    Cost: float | None
    StartDate: date | None
    EndDate: date | None
    Status: ProjectStatus


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
