import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin
from app.models.enums import EmployeeStatus, Gender


class Employee(Base, AuditMixin):
    """Карточка сотрудника. ФИО хранится один раз (Тома 1 §8, принцип №1),
    везде далее используется EmployeeId.

    ИИН/Email отмечены "обязательными" в ТЗ, но остаются nullable на уровне
    БД: у существующих сотрудников этих данных ещё нет, а NOT NULL без
    бэкофилла сломает миграцию. Обязательность — забота EmployeeCreate.
    """

    __tablename__ = "Employees"
    __table_args__ = (
        CheckConstraint("\"IIN\" ~ '^[0-9]{12}$'", name="ck_employees_iin_format"),
    )

    FullName: Mapped[str] = mapped_column(String(255), nullable=False)
    PositionId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Positions.Id"), nullable=True
    )
    OrgUnitId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("OrgUnits.Id"), nullable=True
    )
    HireDate: Mapped[date | None] = mapped_column(Date, nullable=True)
    DismissalDate: Mapped[date | None] = mapped_column(Date, nullable=True)
    Status: Mapped[EmployeeStatus] = mapped_column(
        Enum(EmployeeStatus, name="employee_status"),
        default=EmployeeStatus.ACTIVE,
        nullable=False,
    )

    IIN: Mapped[str | None] = mapped_column(String(12), nullable=True, unique=True)
    Email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    CorporatePhone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    PersonalPhone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    CityId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Cities.Id"), nullable=True
    )
    BirthDate: Mapped[date | None] = mapped_column(Date, nullable=True)
    Gender: Mapped[Gender | None] = mapped_column(
        Enum(Gender, name="gender"), nullable=True
    )
    LegalEntityId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("LegalEntities.Id"), nullable=True
    )
    Salary: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
