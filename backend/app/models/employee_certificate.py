import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin


class CertificationLevel(Base, AuditMixin):
    """Справочник уровней/специализаций аттестата (напр. "По объектам
    второго и третьего уровней ответственности — в части технологического
    оборудования"). Текст длинный и официальный, поэтому Text, а не
    String(255), как у остальных простых справочников.
    """

    __tablename__ = "CertificationLevels"

    Name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)


class EmployeeCertificate(Base, AuditMixin):
    """Аттестат/сертификат сотрудника (PDF). "Версионность" — это просто
    несколько строк на одного сотрудника с разными UploadedDate, отдельной
    цепочки версий не строим. StoredPath — относительный путь под
    FILE_STORAGE_PATH (Тома 1 §7: в БД хранится только ссылка на файл).
    """

    __tablename__ = "EmployeeCertificates"

    EmployeeId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Employees.Id"), nullable=False, index=True
    )
    FileName: Mapped[str] = mapped_column(String(255), nullable=False)
    StoredPath: Mapped[str] = mapped_column(String(500), nullable=False)
    FileSizeBytes: Mapped[int] = mapped_column(Integer, nullable=False)
    CertificateNumber: Mapped[str | None] = mapped_column(String(100), nullable=True)
    CertificationLevelId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("CertificationLevels.Id"), nullable=True
    )
    IssueDate: Mapped[date | None] = mapped_column(Date, nullable=True)
    ExpiryDate: Mapped[date | None] = mapped_column(Date, nullable=True)
    UploadedBy: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=True
    )
    UploadedDate: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
