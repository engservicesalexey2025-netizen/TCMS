import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin


class ProjectDocument(Base, AuditMixin):
    """Файл (PDF) проекта — до 5 штук на проект (см. project_documents.py),
    аналогично EmployeeCertificate. StoredPath — относительный путь под
    FILE_STORAGE_PATH (Тома 1 §7: в БД хранится только ссылка на файл).
    """

    __tablename__ = "ProjectDocuments"

    ProjectId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Projects.Id"), nullable=False, index=True
    )
    FileName: Mapped[str] = mapped_column(String(255), nullable=False)
    StoredPath: Mapped[str] = mapped_column(String(500), nullable=False)
    FileSizeBytes: Mapped[int] = mapped_column(Integer, nullable=False)
    UploadedBy: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=True
    )
    UploadedDate: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
