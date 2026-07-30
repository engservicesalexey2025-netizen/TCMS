import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin
from app.models.enums import ProjectStatus


class ProjectType(Base, AuditMixin):
    """Справочник типов проекта (Тип проекта)."""

    __tablename__ = "ProjectTypes"

    Name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)


class ProjectStage(Base, AuditMixin):
    """Справочник стадий проекта (Стадия проекта)."""

    __tablename__ = "ProjectStages"

    Name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)


class Contour(Base, AuditMixin):
    """Справочник контуров (Контур)."""

    __tablename__ = "Contours"

    Name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)


class ControlSystem(Base, AuditMixin):
    """Справочник систем контроля, в которых отслеживается проект
    (Система контроля) — напр. Opera Build, DES."""

    __tablename__ = "ControlSystems"

    Name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)


class Project(Base, AuditMixin):
    """Проект (ЖК, комплекс) — верхний уровень иерархии карточки объекта
    (Тома 1 §10: Проект → Объект → Пятно → Блок → Этаж). Поля соответствуют
    карточке "Новый объект" (скриншот пользователя): Основные данные,
    Проектные данные, Подрядчики, Договор и характеристики, Даты и ГАСК.
    """

    __tablename__ = "Projects"

    # Основные данные
    Name: Mapped[str] = mapped_column(String(255), nullable=False)
    CityId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Cities.Id"), nullable=True
    )
    Address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    Description: Mapped[str | None] = mapped_column(Text, nullable=True)
    OrgUnitId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("OrgUnits.Id"), nullable=True
    )

    # Проектные данные
    ProjectTypeId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ProjectTypes.Id"), nullable=True
    )
    ProjectStageId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ProjectStages.Id"), nullable=True
    )
    ContourId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Contours.Id"), nullable=True
    )
    ControlSystemId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ControlSystems.Id"), nullable=True
    )
    Status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status"),
        default=ProjectStatus.IN_PROGRESS,
        nullable=False,
    )

    # Подрядчики — все 4 роли ссылаются на один справочник Contractors.
    DeveloperId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Contractors.Id"), nullable=True
    )
    ContractorId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Contractors.Id"), nullable=True
    )
    GeneralContractorId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Contractors.Id"), nullable=True
    )
    SubcontractorId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Contractors.Id"), nullable=True
    )

    # Договор и характеристики
    ContractNumber: Mapped[str | None] = mapped_column(String(100), nullable=True)
    Area: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    Cost: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    GisLink: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Даты и ГАСК
    GaskTicketNumber: Mapped[str | None] = mapped_column(String(100), nullable=True)
    GaskNotificationNumber: Mapped[str | None] = mapped_column(String(100), nullable=True)
    GaskTicketDate: Mapped[date | None] = mapped_column(Date, nullable=True)
    GaskTicketExpiryDate: Mapped[date | None] = mapped_column(Date, nullable=True)
    ActualEndDate: Mapped[date | None] = mapped_column(Date, nullable=True)


class ConstructionObject(Base, AuditMixin):
    """Объект внутри проекта. Пятно/Блок/Этаж — следующий уровень детализации,
    добавляются отдельной миграцией без изменения этой модели (Тома 1А §16
    "развитие без переписывания ядра").
    """

    __tablename__ = "ConstructionObjects"

    ProjectId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Projects.Id"), nullable=False
    )
    Name: Mapped[str] = mapped_column(String(255), nullable=False)
    Address: Mapped[str | None] = mapped_column(String(500), nullable=True)
