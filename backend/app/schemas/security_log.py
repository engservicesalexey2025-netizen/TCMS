import uuid
from datetime import datetime

from pydantic import BaseModel


class SecurityLogEntryOut(BaseModel):
    Id: uuid.UUID
    OccurredAt: datetime
    UserId: uuid.UUID | None = None
    UserLogin: str | None = None
    Action: str
    Result: str
    IpAddress: str | None = None
    UserAgent: str | None = None
    Detail: str | None = None
