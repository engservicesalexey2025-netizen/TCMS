import uuid
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    skip: int
    limit: int


class AuditFields(BaseModel):
    """Common output fields every card exposes (Тома 1А §8)."""

    model_config = ConfigDict(from_attributes=True)

    Id: uuid.UUID
    CreatedDate: datetime
    CreatedBy: uuid.UUID | None = None
    ModifiedDate: datetime
    ModifiedBy: uuid.UUID | None = None
    IsActive: bool
    Version: int
    Comment: str | None = None
