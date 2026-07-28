import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.common import AuditFields


class CertificationLevelCreate(BaseModel):
    Name: str
    Comment: str | None = None


class CertificationLevelOut(AuditFields):
    Name: str


class EmployeeCertificateOut(AuditFields):
    EmployeeId: uuid.UUID
    FileName: str
    FileSizeBytes: int
    CertificateNumber: str | None
    CertificationLevelId: uuid.UUID | None
    IssueDate: date | None
    ExpiryDate: date | None
    UploadedBy: uuid.UUID | None
    UploadedDate: datetime
    # StoredPath намеренно не отдаётся — скачивание только через отдельный эндпоинт.


class EmployeeCertificateUpdate(BaseModel):
    CertificateNumber: str | None = None
    CertificationLevelId: uuid.UUID | None = None
    IssueDate: date | None = None
    ExpiryDate: date | None = None
