import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    requires_mfa: bool = False


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: uuid.UUID
    Code: str
    Name: str


class ModulePermissionsOut(BaseModel):
    actions: list[str]
    columns: list[str]  # ["*"] = без колоночных ограничений для этого модуля


class ViewAsOut(BaseModel):
    OriginalUserId: uuid.UUID
    OriginalLogin: str


class MeOut(BaseModel):
    Id: uuid.UUID
    Login: str
    Email: str
    EmployeeId: uuid.UUID | None = None
    Roles: list[RoleOut]
    MustChangePassword: bool
    Is2FAEnabled: bool
    ViewAs: ViewAsOut | None = None
    Permissions: dict[str, ModulePermissionsOut]


class ChangePasswordIn(BaseModel):
    CurrentPassword: str
    NewPassword: str


class ForgotPasswordIn(BaseModel):
    Email: EmailStr


class ForgotPasswordOut(BaseModel):
    Detail: str


class ResetPasswordIn(BaseModel):
    Token: str
    NewPassword: str


class AdminResetPasswordOut(BaseModel):
    """Временный пароль показывается один раз, как и при одобрении заявки
    на доступ (access_requests.py) — тот же приём переиспользуется здесь,
    пока в системе нет отправки email (§9 ТЗ, решение согласовано с
    заказчиком)."""

    TemporaryPassword: str


class MfaSetupOut(BaseModel):
    Secret: str
    ProvisioningUri: str


class MfaEnableIn(BaseModel):
    Code: str


class MfaEnableOut(BaseModel):
    RecoveryCodes: list[str]


class MfaDisableIn(BaseModel):
    Code: str


class MfaVerifyIn(BaseModel):
    MfaToken: str
    Code: str


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: uuid.UUID
    IssuedAt: datetime
    ExpiresAt: datetime
    IpAddress: str | None = None
    UserAgent: str | None = None
    IsCurrent: bool = False


class LoginHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: uuid.UUID
    LoginAttempted: str
    Success: bool
    Reason: str | None = None
    IpAddress: str | None = None
    CreatedDate: datetime


class ViewAsIn(BaseModel):
    Reason: str | None = None


class DelegationCreateIn(BaseModel):
    ToUserId: uuid.UUID
    RoleId: uuid.UUID | None = None
    ExpiresAt: datetime
    Reason: str | None = None


class DelegationOut(BaseModel):
    Id: uuid.UUID
    FromUserId: uuid.UUID
    ToUserId: uuid.UUID
    ToUserLogin: str | None = None
    RoleId: uuid.UUID | None = None
    StartsAt: datetime
    ExpiresAt: datetime
    Reason: str | None = None
