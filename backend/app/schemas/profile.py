import uuid
from datetime import datetime

from pydantic import BaseModel


class ActiveProjectOut(BaseModel):
    Id: uuid.UUID
    Name: str


class ProfileOut(BaseModel):
    Id: uuid.UUID
    Login: str
    Email: str
    FullName: str | None = None
    Position: str | None = None
    OrgUnit: str | None = None
    CorporatePhone: str | None = None
    LastLoginAt: datetime | None = None
    Roles: list[str]
    ActiveProjects: list[ActiveProjectOut]
