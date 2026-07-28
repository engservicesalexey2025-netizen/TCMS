import uuid

from pydantic import BaseModel, EmailStr

from app.models.enums import AccessRequestStatus
from app.schemas.common import AuditFields


class AccessRequestCreate(BaseModel):
    FullName: str
    Email: EmailStr
    RequestedRoleId: uuid.UUID
    RequestedOrgUnitId: uuid.UUID | None = None
    Comment: str | None = None


class AccessRequestDecision(BaseModel):
    Approve: bool
    Login: str | None = None
    TemporaryPassword: str | None = None


class AccessRequestOut(AuditFields):
    FullName: str
    Email: str
    RequestedRoleId: uuid.UUID
    RequestedOrgUnitId: uuid.UUID | None
    Status: AccessRequestStatus
    DecidedByUserId: uuid.UUID | None
    CreatedUserId: uuid.UUID | None
