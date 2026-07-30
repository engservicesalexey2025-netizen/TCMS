import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin


class AssignmentRole(Base, AuditMixin):
    """Справочник ролей на проекте (Роль на проекте) — напр. Технический
    надзор, Контроль качества."""

    __tablename__ = "AssignmentRoles"

    Name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)


class Assignment(Base, AuditMixin):
    """Назначение сотрудника на проект (нагрузка): роль на проекте, ставка,
    период — связующая сущность, превращающая Employees/Projects в
    реляционную модель нагрузок (наследие Плана Sheets Dashboard §2).

    Отсутствие PeriodEnd означает, что сотрудник — действующий специалист на
    проекте (ещё не завершил работу над ним).
    """

    __tablename__ = "Assignments"

    EmployeeId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Employees.Id"), nullable=False
    )
    ProjectId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Projects.Id"), nullable=False
    )
    RoleOnProjectId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("AssignmentRoles.Id"), nullable=True
    )
    Workload: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True, comment="Ставка/загрузка, напр. 0.5 = 50%"
    )
    PeriodStart: Mapped[date | None] = mapped_column(Date, nullable=True)
    PeriodEnd: Mapped[date | None] = mapped_column(Date, nullable=True)
