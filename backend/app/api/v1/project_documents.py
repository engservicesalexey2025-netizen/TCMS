import re
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select

from app.api.deps import DbSession, require_permission
from app.models.enums import AuditAction
from app.models.project import Project
from app.models.project_document import ProjectDocument
from app.models.user import User
from app.schemas.common import Page
from app.schemas.project_document import ProjectDocumentOut
from app.services import file_storage
from app.services.audit import log_action
from app.services.crud_base import AuditedRepository

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["project-documents"])

repo = AuditedRepository(ProjectDocument)

MAX_DOCUMENT_SIZE_BYTES = 10 * 1024 * 1024
MAX_DOCUMENTS_PER_PROJECT = 5
PDF_MAGIC = b"%PDF-"
CHUNK_SIZE = 1024 * 1024

ViewUser = Annotated[User, Depends(require_permission("PROJECT_DOCUMENTS", "VIEW"))]
WriteUser = Annotated[User, Depends(require_permission("PROJECT_DOCUMENTS", "UPDATE"))]


def _get_project_or_404(db, project_id: uuid.UUID) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Проект не найден")
    return project


def _get_document_or_404(db, project_id: uuid.UUID, doc_id: uuid.UUID) -> ProjectDocument:
    doc = repo.get(db, doc_id)
    if doc is None or doc.ProjectId != project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Файл не найден")
    return doc


def _safe_filename(original: str) -> str:
    name = Path(original).name
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return name[:200] or "file.pdf"


def _active_document_count(db, project_id: uuid.UUID) -> int:
    return len(
        db.scalars(
            select(ProjectDocument).where(
                ProjectDocument.ProjectId == project_id,
                ProjectDocument.IsActive.is_(True),
            )
        ).all()
    )


@router.post("", response_model=ProjectDocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: uuid.UUID,
    db: DbSession,
    user: WriteUser,
    file: UploadFile,
):
    _get_project_or_404(db, project_id)

    if _active_document_count(db, project_id) >= MAX_DOCUMENTS_PER_PROJECT:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Достигнут лимит файлов на проект ({MAX_DOCUMENTS_PER_PROJECT})",
        )

    body = bytearray()
    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break
        body.extend(chunk)
        if len(body) > MAX_DOCUMENT_SIZE_BYTES:
            raise HTTPException(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                f"Файл превышает лимит {MAX_DOCUMENT_SIZE_BYTES // (1024 * 1024)} МБ",
            )

    if not bytes(body[: len(PDF_MAGIC)]) == PDF_MAGIC:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Файл не является корректным PDF (сигнатура не совпадает)"
        )

    safe_name = _safe_filename(file.filename or "document.pdf")
    relative_path = f"projects/{project_id}/{uuid.uuid4()}_{safe_name}"
    file_storage.save(relative_path, bytes(body))

    obj = repo.create(
        db,
        {
            "ProjectId": project_id,
            "FileName": file.filename or safe_name,
            "StoredPath": relative_path,
            "FileSizeBytes": len(body),
            "UploadedBy": user.Id,
        },
        user.Id,
    )
    return ProjectDocumentOut.model_validate(obj, from_attributes=True)


@router.get("", response_model=Page[ProjectDocumentOut])
def list_documents(
    project_id: uuid.UUID,
    db: DbSession,
    _user: ViewUser,
    skip: int = 0,
    limit: int = 50,
):
    _get_project_or_404(db, project_id)
    query = select(ProjectDocument).where(
        ProjectDocument.ProjectId == project_id,
        ProjectDocument.IsActive.is_(True),
    )
    rows = db.scalars(query.offset(skip).limit(limit)).all()
    total = len(db.scalars(query).all())
    return Page(
        items=[ProjectDocumentOut.model_validate(r, from_attributes=True) for r in rows],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{doc_id}/download")
def download_document(
    project_id: uuid.UUID, doc_id: uuid.UUID, db: DbSession, _user: ViewUser
):
    doc = _get_document_or_404(db, project_id, doc_id)
    data = file_storage.read(doc.StoredPath)
    if data is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Файл не найден в хранилище")
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{doc.FileName}"'},
    )


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(project_id: uuid.UUID, doc_id: uuid.UUID, db: DbSession, user: WriteUser):
    """Настоящее удаление (не архивирование), как и для аттестатов сотрудников —
    убирает и строку в БД, и файл на диске, факт фиксируется в AuditLog."""
    doc = _get_document_or_404(db, project_id, doc_id)

    log_action(
        db,
        table_name="ProjectDocuments",
        record_id=doc.Id,
        action=AuditAction.DELETE,
        user_id=user.Id,
        field_name="FileName",
        old_value=doc.FileName,
        new_value=None,
    )
    db.delete(doc)
    db.commit()

    file_storage.delete(doc.StoredPath)
