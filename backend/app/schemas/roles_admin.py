import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RoleAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: uuid.UUID
    Code: str
    Name: str
    IsSystem: bool
    BypassDataScope: bool


class RoleCreateIn(BaseModel):
    Code: str
    Name: str


class RoleUpdateIn(BaseModel):
    Name: str


class RoleCloneIn(BaseModel):
    NewCode: str
    NewName: str


class PermissionMatrixEntryOut(BaseModel):
    Module: str
    Action: str
    Granted: bool


class PermissionGrantIn(BaseModel):
    Module: str
    Action: str
    Granted: bool


class ColumnPermissionEntryOut(BaseModel):
    FieldName: str
    Mode: str


class ColumnPermissionsIn(BaseModel):
    EntityName: str
    Fields: list[ColumnPermissionEntryOut]


class UserRoleAssignmentIn(BaseModel):
    RoleId: uuid.UUID
    ExpiresAt: datetime | None = None


class UserRoleAssignmentOut(BaseModel):
    RoleId: uuid.UUID
    RoleName: str
    ExpiresAt: datetime | None = None


class UserPermissionOverrideIn(BaseModel):
    Module: str
    Action: str
    Effect: str  # GRANT | DENY
    ExpiresAt: datetime | None = None
    Reason: str | None = None


class UserPermissionOverrideOut(BaseModel):
    Module: str
    Action: str
    Effect: str
    ExpiresAt: datetime | None = None
    Reason: str | None = None


class UserOrgAccessIn(BaseModel):
    OrgUnitId: uuid.UUID
    ExpiresAt: datetime | None = None


class UserOrgAccessOut(BaseModel):
    OrgUnitId: uuid.UUID
    OrgUnitName: str
    ExpiresAt: datetime | None = None


class UserDataScopeIn(BaseModel):
    ScopeType: str
    ScopeId: uuid.UUID
    ExpiresAt: datetime | None = None
    Reason: str | None = None


class UserDataScopeOut(BaseModel):
    ScopeType: str
    ScopeId: uuid.UUID
    ExpiresAt: datetime | None = None
    Reason: str | None = None


class UserSummaryOut(BaseModel):
    Id: uuid.UUID
    Login: str
    Email: str
    IsActive: bool
    Roles: list[str]


class UserDetailOut(BaseModel):
    Id: uuid.UUID
    Login: str
    Email: str
    IsActive: bool
    MustChangePassword: bool
    MfaEnabled: bool
    Roles: list[UserRoleAssignmentOut]
    PermissionOverrides: list[UserPermissionOverrideOut]
    OrgAccess: list[UserOrgAccessOut]
    DataScopes: list[UserDataScopeOut]
