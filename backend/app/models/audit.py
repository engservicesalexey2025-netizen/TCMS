import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import AuditAction


class AuditLog(Base):
    """Журнал изменений (Тома 1А §11): кто/когда/что/старое→новое/IP.
    Не использует AuditMixin — сама является историей, а не бизнес-сущностью.
    """

    __tablename__ = "AuditLog"

    Id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    TableName: Mapped[str] = mapped_column(String(100), nullable=False)
    RecordId: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    Action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, name="audit_action"), nullable=False
    )
    ChangedByUserId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=True
    )
    ChangedDate: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    FieldName: Mapped[str | None] = mapped_column(String(100), nullable=True)
    OldValue: Mapped[str | None] = mapped_column(Text, nullable=True)
    NewValue: Mapped[str | None] = mapped_column(Text, nullable=True)
    IpAddress: Mapped[str | None] = mapped_column(String(45), nullable=True)
