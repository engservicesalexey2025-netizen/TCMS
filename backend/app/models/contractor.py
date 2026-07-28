from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin


class Contractor(Base, AuditMixin):
    """Справочник подрядчиков."""

    __tablename__ = "Contractors"

    Name: Mapped[str] = mapped_column(String(255), nullable=False)
    BinIin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ContactInfo: Mapped[str | None] = mapped_column(String(500), nullable=True)
