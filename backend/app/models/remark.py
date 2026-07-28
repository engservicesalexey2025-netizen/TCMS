import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin
from app.models.enums import RemarkStatus


class Remark(Base, AuditMixin):
    """Замечание технадзора по объекту — первая операционная сущность,
    на которой обкатывается полный паттерн карточки: связи по ID,
    статус-жизненный цикл, аудит через AuditLog.
    """

    __tablename__ = "Remarks"

    ObjectId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ConstructionObjects.Id"), nullable=False
    )
    ContractorId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Contractors.Id"), nullable=True
    )
    ResponsibleEmployeeId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Employees.Id"), nullable=True
    )
    Title: Mapped[str] = mapped_column(String(255), nullable=False)
    Description: Mapped[str | None] = mapped_column(Text, nullable=True)
    Status: Mapped[RemarkStatus] = mapped_column(
        Enum(RemarkStatus, name="remark_status"),
        default=RemarkStatus.NEW,
        nullable=False,
    )
    DueDate: Mapped[date | None] = mapped_column(Date, nullable=True)
    ResolvedDate: Mapped[date | None] = mapped_column(Date, nullable=True)
