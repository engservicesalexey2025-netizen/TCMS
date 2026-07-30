import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import AuditFields


class ProjectDocumentOut(AuditFields):
    ProjectId: uuid.UUID
    FileName: str
    FileSizeBytes: int
    UploadedBy: uuid.UUID | None
    UploadedDate: datetime
    # StoredPath намеренно не отдаётся — скачивание только через отдельный эндпоинт.
