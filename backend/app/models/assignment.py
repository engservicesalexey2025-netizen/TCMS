import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin


class Assignment(Base, AuditMixin):
    """Назначение сотрудника на проект (нагрузка): роль на проекте, ставка,
    период — связующая сущность, превращающая Employees/Projects в
    реляционную модель нагрузок (наследие Плана Sheets Dashboard §2).
    """

    __tablename__ = "Assignments"

    EmployeeId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Employees.Id"), nullable=False
    )
    ProjectId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Projects.Id"), nullable=False
    )
    RoleOnProject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    Workload: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True, comment="Ставка/загрузка, напр. 0.5 = 50%"
    )
    PeriodStart: Mapped[date | None] = mapped_column(Date, nullable=True)
    PeriodEnd: Mapped[date | None] = mapped_column(Date, nullable=True)
