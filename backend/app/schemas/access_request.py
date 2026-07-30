import uuid

from pydantic import BaseModel, EmailStr

from app.models.enums import AccessRequestStatus
from app.schemas.common import AuditFields


class AccessRequestCreate(BaseModel):
    FullName: str
    Email: EmailStr
    Phone: str | None = None
    Organization: str | None = None
    Position: str | None = None
    RequestedRoleId: uuid.UUID
    RequestedOrgUnitId: uuid.UUID | None = None
    RequestedProjectId: uuid.UUID | None = None
    Comment: str | None = None


class AccessRequestDecision(BaseModel):
    Approve: bool
    # Пусто = использовать RequestedRoleId заявки как единственную роль —
    # админ может выдать несколько ролей сразу, не ограничиваясь тем, что
    # выбрал заявитель (§5 ТЗ, шаг "Назначить роль(-и)").
    RoleIds: list[uuid.UUID] | None = None
    Login: str | None = None
    TemporaryPassword: str | None = None


class AccessRequestOut(AuditFields):
    FullName: str
    Email: str
    Phone: str | None
    Organization: str | None
    Position: str | None
    RequestedRoleId: uuid.UUID
    RequestedOrgUnitId: uuid.UUID | None
    RequestedProjectId: uuid.UUID | None
    Status: AccessRequestStatus
    DecidedByUserId: uuid.UUID | None
    CreatedUserId: uuid.UUID | None
