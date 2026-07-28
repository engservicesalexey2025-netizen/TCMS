"""Shared audit mixin.

Per Tom 1A (§8 "Обязательные поля каждой таблицы") every business table must
carry: Id, CreatedDate, CreatedBy, ModifiedDate, ModifiedBy, IsActive,
Version, Comment. Deletion is forbidden (§10 "Архивирование") — IsActive
is flipped instead, history lives in AuditLog (§11).
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class AuditMixin:
    Id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    CreatedDate: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    CreatedBy: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=True
    )
    ModifiedDate: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    ModifiedBy: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=True
    )
    IsActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    Version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    Comment: Mapped[str | None] = mapped_column(Text, nullable=True)
