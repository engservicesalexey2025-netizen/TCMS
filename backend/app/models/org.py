import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin
from app.models.enums import OrgUnitType


class OrgUnit(Base, AuditMixin):
    """Организационная единица: Дивизион / Управление / Группа.

    Самоссылающаяся иерархия вместо трёх разных таблиц — упрощает обход
    дерева и добавление новых уровней без миграций.
    """

    __tablename__ = "OrgUnits"

    Name: Mapped[str] = mapped_column(String(255), nullable=False)
    UnitType: Mapped[OrgUnitType] = mapped_column(
        Enum(OrgUnitType, name="org_unit_type"), nullable=False
    )
    ParentOrgUnitId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("OrgUnits.Id"), nullable=True
    )

    Parent: Mapped["OrgUnit | None"] = relationship(
        remote_side="OrgUnit.Id", back_populates="Children"
    )
    Children: Mapped[list["OrgUnit"]] = relationship(back_populates="Parent")


class Position(Base, AuditMixin):
    """Справочник должностей."""

    __tablename__ = "Positions"

    Name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)


class City(Base, AuditMixin):
    """Справочник городов (место работы)."""

    __tablename__ = "Cities"

    Name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)


class LegalEntity(Base, AuditMixin):
    """Справочник юридических лиц (ТОО)."""

    __tablename__ = "LegalEntities"

    Name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
