import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin
from app.models.enums import ProjectStatus


class Project(Base, AuditMixin):
    """Проект (ЖК, комплекс) — верхний уровень иерархии карточки объекта
    (Тома 1 §10: Проект → Объект → Пятно → Блок → Этаж).
    """

    __tablename__ = "Projects"

    Name: Mapped[str] = mapped_column(String(255), nullable=False)
    OrgUnitId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("OrgUnits.Id"), nullable=True
    )
    Area: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    Cost: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    StartDate: Mapped[date | None] = mapped_column(Date, nullable=True)
    EndDate: Mapped[date | None] = mapped_column(Date, nullable=True)
    Status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status"),
        default=ProjectStatus.PLANNED,
        nullable=False,
    )


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
