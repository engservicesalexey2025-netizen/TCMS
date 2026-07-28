import uuid
from datetime import date

from pydantic import BaseModel

from app.schemas.common import AuditFields


class AssignmentCreate(BaseModel):
    EmployeeId: uuid.UUID
    ProjectId: uuid.UUID
    RoleOnProject: str | None = None
    Workload: float | None = None
    PeriodStart: date | None = None
    PeriodEnd: date | None = None
    Comment: str | None = None


class AssignmentUpdate(BaseModel):
    RoleOnProject: str | None = None
    Workload: float | None = None
    PeriodStart: date | None = None
    PeriodEnd: date | None = None
    Comment: str | None = None


class AssignmentOut(AuditFields):
    EmployeeId: uuid.UUID
    ProjectId: uuid.UUID
    RoleOnProject: str | None
    Workload: float | None
    PeriodStart: date | None
    PeriodEnd: date | None
