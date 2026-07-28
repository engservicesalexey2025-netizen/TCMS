"""Import session tracking.

Like AuditLog, these are history/process records rather than business
entities — no AuditMixin, no archiving. ImportRow.MatchedRecordId is a bare
UUID with no FK constraint (same reasoning as AuditLog.RecordId): it can
point at Employees, Positions, or whatever entity a future import profile
targets, so a single FK target doesn't make sense.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import (
    ImportRowAppliedAction,
    ImportRowClassification,
    ImportRowDecision,
    ImportSessionStatus,
)


class ImportSession(Base):
    __tablename__ = "ImportSessions"

    Id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    EntityType: Mapped[str] = mapped_column(String(100), nullable=False)
    FileName: Mapped[str] = mapped_column(String(255), nullable=False)
    Status: Mapped[ImportSessionStatus] = mapped_column(
        Enum(ImportSessionStatus, name="import_session_status"),
        default=ImportSessionStatus.UPLOADED,
        nullable=False,
    )
    ColumnMapping: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    CreatedBy: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=True
    )
    CreatedDate: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    AppliedBy: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=True
    )
    AppliedDate: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ErrorMessage: Mapped[str | None] = mapped_column(Text, nullable=True)


class ImportRow(Base):
    __tablename__ = "ImportRows"

    Id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ImportSessionId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ImportSessions.Id"), nullable=False
    )
    RowNumber: Mapped[int] = mapped_column(Integer, nullable=False)
    RawData: Mapped[dict] = mapped_column(JSONB, nullable=False)
    NormalizedData: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    MatchedRecordId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    MatchedRecordVersion: Mapped[int | None] = mapped_column(Integer, nullable=True)
    Classification: Mapped[ImportRowClassification] = mapped_column(
        Enum(ImportRowClassification, name="import_row_classification"),
        nullable=False,
    )
    DiffFields: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ValidationError: Mapped[str | None] = mapped_column(Text, nullable=True)
    Decision: Mapped[ImportRowDecision] = mapped_column(
        Enum(ImportRowDecision, name="import_row_decision"),
        default=ImportRowDecision.PENDING,
        nullable=False,
    )
    AppliedAction: Mapped[ImportRowAppliedAction | None] = mapped_column(
        Enum(ImportRowAppliedAction, name="import_row_applied_action"),
        nullable=True,
    )
    AppliedError: Mapped[str | None] = mapped_column(Text, nullable=True)
    AppliedDate: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
