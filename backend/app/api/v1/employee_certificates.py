import re
import uuid
from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, require_roles
from app.api.v1.crud_router import build_crud_router
from app.core.config import settings
from app.models.employee import Employee
from app.models.employee_certificate import CertificationLevel, EmployeeCertificate
from app.models.enums import AuditAction, RoleCode
from app.models.user import User
from app.schemas.common import Page
from app.schemas.employee_certificate import (
    CertificationLevelCreate,
    CertificationLevelOut,
    EmployeeCertificateOut,
    EmployeeCertificateUpdate,
)
from app.services.audit import log_action
from app.services.crud_base import AuditedRepository
from app.services.masking import FULL_PII_ROLES

router = APIRouter(prefix="/employees/{employee_id}/certificates", tags=["employee-certificates"])

repo = AuditedRepository(EmployeeCertificate)

certification_levels_router = build_crud_router(
    model=CertificationLevel,
    create_schema=CertificationLevelCreate,
    update_schema=CertificationLevelCreate,
    out_schema=CertificationLevelOut,
    prefix="/certification-levels",
    tags=["certification-levels"],
    search_fields=["Name"],
    write_roles=(RoleCode.ADMIN,),
)

MAX_CERTIFICATE_SIZE_BYTES = 10 * 1024 * 1024
PDF_MAGIC = b"%PDF-"
CHUNK_SIZE = 1024 * 1024

WriteUser = Annotated[User, Depends(require_roles(*FULL_PII_ROLES))]
DownloadUser = Annotated[User, Depends(require_roles(*FULL_PII_ROLES))]

STORAGE_ROOT = Path(settings.FILE_STORAGE_PATH).resolve()


def _get_employee_or_404(db, employee_id: uuid.UUID) -> Employee:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Сотрудник не найден")
    return employee


def _get_certificate_or_404(db, employee_id: uuid.UUID, cert_id: uuid.UUID) -> EmployeeCertificate:
    cert = repo.get(db, cert_id)
    if cert is None or cert.EmployeeId != employee_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Аттестат не найден")
    return cert


def _safe_filename(original: str) -> str:
    name = Path(original).name
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return name[:200] or "file.pdf"


@router.post("", response_model=EmployeeCertificateOut, status_code=status.HTTP_201_CREATED)
async def upload_certificate(
    employee_id: uuid.UUID,
    db: DbSession,
    user: WriteUser,
    file: UploadFile,
    certificate_number: Annotated[str | None, Form()] = None,
    certification_level_id: Annotated[uuid.UUID | None, Form()] = None,
    issue_date: Annotated[date | None, Form()] = None,
):
    _get_employee_or_404(db, employee_id)

    body = bytearray()
    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break
        body.extend(chunk)
        if len(body) > MAX_CERTIFICATE_SIZE_BYTES:
            raise HTTPException(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                f"Файл превышает лимит {MAX_CERTIFICATE_SIZE_BYTES // (1024 * 1024)} МБ",
            )

    if not bytes(body[: len(PDF_MAGIC)]) == PDF_MAGIC:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Файл не является корректным PDF (сигнатура не совпадает)"
        )

    safe_name = _safe_filename(file.filename or "certificate.pdf")
    relative_path = f"certificates/{employee_id}/{uuid.uuid4()}_{safe_name}"
    final_path = (STORAGE_ROOT / relative_path).resolve()
    if not final_path.is_relative_to(STORAGE_ROOT):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Недопустимое имя файла")

    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_bytes(bytes(body))

    obj = repo.create(
        db,
        {
            "EmployeeId": employee_id,
            "FileName": file.filename or safe_name,
            "StoredPath": relative_path,
            "FileSizeBytes": len(body),
            "CertificateNumber": certificate_number,
            "CertificationLevelId": certification_level_id,
            "IssueDate": issue_date,
            "UploadedBy": user.Id,
        },
        user.Id,
    )
    return EmployeeCertificateOut.model_validate(obj, from_attributes=True)


@router.get("", response_model=Page[EmployeeCertificateOut])
def list_certificates(
    employee_id: uuid.UUID,
    db: DbSession,
    _user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
):
    _get_employee_or_404(db, employee_id)
    query = select(EmployeeCertificate).where(
        EmployeeCertificate.EmployeeId == employee_id,
        EmployeeCertificate.IsActive.is_(True),
    )
    rows = db.scalars(query.offset(skip).limit(limit)).all()
    total = len(db.scalars(query).all())
    return Page(
        items=[EmployeeCertificateOut.model_validate(r, from_attributes=True) for r in rows],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{cert_id}/download")
def download_certificate(
    employee_id: uuid.UUID, cert_id: uuid.UUID, db: DbSession, _user: DownloadUser
):
    cert = _get_certificate_or_404(db, employee_id, cert_id)
    full_path = (STORAGE_ROOT / cert.StoredPath).resolve()
    if not full_path.is_relative_to(STORAGE_ROOT) or not full_path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Файл не найден на диске")
    return FileResponse(full_path, media_type="application/pdf", filename=cert.FileName)


@router.patch("/{cert_id}", response_model=EmployeeCertificateOut)
def update_certificate(
    employee_id: uuid.UUID,
    cert_id: uuid.UUID,
    data: EmployeeCertificateUpdate,
    db: DbSession,
    user: WriteUser,
):
    _get_certificate_or_404(db, employee_id, cert_id)
    obj = repo.update(db, cert_id, data.model_dump(exclude_unset=True), user.Id)
    return EmployeeCertificateOut.model_validate(obj, from_attributes=True)


@router.delete("/{cert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_certificate(
    employee_id: uuid.UUID, cert_id: uuid.UUID, db: DbSession, user: WriteUser
):
    """Настоящее удаление (не архивирование) — по явному запросу пользователя
    для этого конкретного типа вложения. Удаляет и строку в БД, и файл на
    диске; факт удаления фиксируется в AuditLog (кто/когда/какой файл), хотя
    сама запись после удаления восстановить нельзя.
    """
    cert = _get_certificate_or_404(db, employee_id, cert_id)
    full_path = (STORAGE_ROOT / cert.StoredPath).resolve()

    log_action(
        db,
        table_name="EmployeeCertificates",
        record_id=cert.Id,
        action=AuditAction.DELETE,
        user_id=user.Id,
        field_name="FileName",
        old_value=cert.FileName,
        new_value=None,
    )
    db.delete(cert)
    db.commit()

    if full_path.is_relative_to(STORAGE_ROOT) and full_path.is_file():
        full_path.unlink(missing_ok=True)
