import uuid
from datetime import date

from pydantic import BaseModel

from app.schemas.common import AuditFields


class AssignmentRoleCreate(BaseModel):
    Name: str
    Comment: str | None = None


class AssignmentRoleOut(AuditFields):
    Name: str


class AssignmentCreate(BaseModel):
    EmployeeId: uuid.UUID
    ProjectId: uuid.UUID
    RoleOnProjectId: uuid.UUID | None = None
    Workload: float | None = None
    PeriodStart: date | None = None
    PeriodEnd: date | None = None
    Comment: str | None = None


class AssignmentUpdate(BaseModel):
    RoleOnProjectId: uuid.UUID | None = None
    Workload: float | None = None
    PeriodStart: date | None = None
    PeriodEnd: date | None = None
    Comment: str | None = None


class AssignmentOut(AuditFields):
    EmployeeId: uuid.UUID
    ProjectId: uuid.UUID
    RoleOnProjectId: uuid.UUID | None
    Workload: float | None
    PeriodStart: date | None
    PeriodEnd: date | None
