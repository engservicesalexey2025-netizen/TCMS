import uuid

from fastapi import APIRouter, HTTPException, Response, UploadFile, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.services.permissions import user_has_permission
from app.models.enums import ImportRowClassification, ImportRowDecision, ImportSessionStatus
from app.models.import_session import ImportRow, ImportSession
from app.schemas.common import Page
from app.schemas.import_session import (
    ApplyResult,
    BulkRowDecisionUpdate,
    ImportRowOut,
    ImportSessionOut,
    RowDecisionUpdate,
)
from app.services.import_profiles import get_profile
from app.services.import_service import (
    apply_session,
    generate_template,
    parse_and_stage,
    session_counts,
    set_row_decision,
)

router = APIRouter(prefix="/imports", tags=["imports"])


def _require_profile(entity_type: str):
    profile = get_profile(entity_type)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Неизвестный тип импорта: {entity_type}")
    return profile


def _require_write_access(profile, db, user) -> None:
    if not user_has_permission(db, user, profile.module, "IMPORT"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Недостаточно прав для импорта этой сущности")


def _to_session_out(session: ImportSession, db) -> ImportSessionOut:
    profile = get_profile(session.EntityType)
    columns = (
        [{"field": c.field, "header": c.header_aliases[0]} for c in profile.columns]
        if profile
        else []
    )
    return ImportSessionOut(
        Id=session.Id,
        EntityType=session.EntityType,
        FileName=session.FileName,
        Status=session.Status,
        CreatedBy=session.CreatedBy,
        CreatedDate=session.CreatedDate,
        AppliedBy=session.AppliedBy,
        AppliedDate=session.AppliedDate,
        ErrorMessage=session.ErrorMessage,
        Counts=session_counts(db, session.Id),
        Columns=columns,
    )


def _get_session_or_404(db, session_id: uuid.UUID) -> ImportSession:
    session = db.get(ImportSession, session_id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Сессия импорта не найдена")
    return session


@router.get("/{entity_type}/template")
def download_template(entity_type: str, _user: CurrentUser):
    profile = _require_profile(entity_type)
    content = generate_template(profile)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{entity_type}_template.xlsx"'},
    )


@router.post(
    "/{entity_type}/sessions", response_model=ImportSessionOut, status_code=status.HTTP_201_CREATED
)
async def upload_session(
    entity_type: str, db: DbSession, user: CurrentUser, file: UploadFile
) -> ImportSessionOut:
    profile = _require_profile(entity_type)
    _require_write_access(profile, db, user)
    file_bytes = await file.read()
    session = parse_and_stage(db, profile, file_bytes, file.filename or "upload.xlsx", user.Id)
    return _to_session_out(session, db)


@router.get("/sessions", response_model=Page[ImportSessionOut])
def list_sessions(
    db: DbSession,
    _user: CurrentUser,
    entity_type: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> Page[ImportSessionOut]:
    query = select(ImportSession)
    if entity_type:
        query = query.where(ImportSession.EntityType == entity_type)
    query = query.order_by(ImportSession.CreatedDate.desc())
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.offset(skip).limit(limit)).all()
    return Page(
        items=[_to_session_out(s, db) for s in rows], total=total, skip=skip, limit=limit
    )


@router.get("/sessions/{session_id}", response_model=ImportSessionOut)
def get_session(session_id: uuid.UUID, db: DbSession, _user: CurrentUser) -> ImportSessionOut:
    session = _get_session_or_404(db, session_id)
    return _to_session_out(session, db)


@router.get("/sessions/{session_id}/rows", response_model=Page[ImportRowOut])
def list_session_rows(
    session_id: uuid.UUID,
    db: DbSession,
    _user: CurrentUser,
    classification: ImportRowClassification | None = None,
    decision: ImportRowDecision | None = None,
    skip: int = 0,
    limit: int = 50,
) -> Page[ImportRowOut]:
    _get_session_or_404(db, session_id)
    query = select(ImportRow).where(ImportRow.ImportSessionId == session_id)
    if classification is not None:
        query = query.where(ImportRow.Classification == classification)
    if decision is not None:
        query = query.where(ImportRow.Decision == decision)
    query = query.order_by(ImportRow.RowNumber)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.offset(skip).limit(limit)).all()
    return Page(items=list(rows), total=total, skip=skip, limit=limit)


@router.patch("/sessions/{session_id}/rows/{row_id}/decision", response_model=ImportRowOut)
def update_row_decision(
    session_id: uuid.UUID,
    row_id: uuid.UUID,
    data: RowDecisionUpdate,
    db: DbSession,
    user: CurrentUser,
) -> ImportRowOut:
    session = _get_session_or_404(db, session_id)
    profile = _require_profile(session.EntityType)
    _require_write_access(profile, db, user)
    row = db.get(ImportRow, row_id)
    if row is None or row.ImportSessionId != session_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Строка не найдена")
    try:
        return set_row_decision(db, row, data.decision)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))


@router.post("/sessions/{session_id}/rows/bulk-decision", response_model=list[ImportRowOut])
def bulk_update_row_decision(
    session_id: uuid.UUID, data: BulkRowDecisionUpdate, db: DbSession, user: CurrentUser
) -> list[ImportRowOut]:
    session = _get_session_or_404(db, session_id)
    profile = _require_profile(session.EntityType)
    _require_write_access(profile, db, user)

    query = select(ImportRow).where(ImportRow.ImportSessionId == session_id)
    if data.row_ids:
        query = query.where(ImportRow.Id.in_(data.row_ids))
    if data.classification is not None:
        query = query.where(ImportRow.Classification == data.classification)
    rows = db.scalars(query).all()

    updated = []
    for row in rows:
        try:
            updated.append(set_row_decision(db, row, data.decision))
        except ValueError:
            continue
    return updated


@router.post("/sessions/{session_id}/apply", response_model=ApplyResult)
def apply(session_id: uuid.UUID, db: DbSession, user: CurrentUser) -> ApplyResult:
    session = _get_session_or_404(db, session_id)
    profile = _require_profile(session.EntityType)
    _require_write_access(profile, db, user)
    try:
        result = apply_session(db, session, user.Id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return ApplyResult(**result)


@router.post("/sessions/{session_id}/cancel", response_model=ImportSessionOut)
def cancel_session(session_id: uuid.UUID, db: DbSession, user: CurrentUser) -> ImportSessionOut:
    session = _get_session_or_404(db, session_id)
    profile = _require_profile(session.EntityType)
    _require_write_access(profile, db, user)

    if session.Status not in (ImportSessionStatus.UPLOADED, ImportSessionStatus.REVIEW):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Сессию в этом статусе нельзя отменить")
    session.Status = ImportSessionStatus.CANCELLED
    db.commit()
    return _to_session_out(session, db)
