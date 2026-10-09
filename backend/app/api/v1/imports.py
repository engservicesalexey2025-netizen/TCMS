import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession, require_superadmin
from app.models.user import User
from app.services.permissions import user_has_permission
from app.models.enums import ImportRowClassification, ImportRowDecision, ImportSessionStatus
from app.models.import_session import ImportRow, ImportSession
from app.schemas.common import Page
from app.schemas.import_session import (
    ApplyResult,
    BulkRowDecisionUpdate,
    ImportRowOut,
    ImportSessionOut,
    RowDataUpdate,
    RowDecisionUpdate,
)
from app.services.import_profiles import get_profile
from app.services.import_service import (
    apply_session,
    generate_template,
    parse_and_stage,
    revalidate_row,
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


def _column_meta(col, db) -> dict:
    meta = {
        "field": col.field,
        "header": col.header_aliases[0],
        "kind": col.kind,
        "required": col.required,
    }
    if col.kind == "enum" and col.enum_map:
        meta["options"] = list(col.enum_map.keys())
    elif col.kind == "fk_lookup" and col.fk_model is not None:
        names = db.scalars(
            select(getattr(col.fk_model, col.fk_lookup_field))
            .where(col.fk_model.IsActive.is_(True))
            .order_by(getattr(col.fk_model, col.fk_lookup_field))
        ).all()
        meta["options"] = list(names)
    return meta


def _to_session_out(session: ImportSession, db) -> ImportSessionOut:
    profile = get_profile(session.EntityType)
    columns = [_column_meta(c, db) for c in profile.columns] if profile else []
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
        return set_row_decision(db, session, row, data.decision, user.Id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))


@router.patch("/sessions/{session_id}/rows/{row_id}", response_model=ImportRowOut)
def edit_row(
    session_id: uuid.UUID,
    row_id: uuid.UUID,
    data: RowDataUpdate,
    db: DbSession,
    user: CurrentUser,
) -> ImportRowOut:
    """Ручное исправление строки в разделе «Ошибки»: правки применяются к
    исходным данным строки, после чего она заново нормализуется и
    классифицируется — принять её (см. update_row_decision) можно сразу же,
    без повторного импорта файла."""
    session = _get_session_or_404(db, session_id)
    profile = _require_profile(session.EntityType)
    _require_write_access(profile, db, user)
    row = db.get(ImportRow, row_id)
    if row is None or row.ImportSessionId != session_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Строка не найдена")
    return revalidate_row(db, profile, row, data.data)


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
            updated.append(set_row_decision(db, session, row, data.decision, user.Id))
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


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: uuid.UUID, db: DbSession, user: CurrentUser) -> None:
    """История импорта — не бизнес-данные (см. докстринг ImportSession), поэтому
    здесь настоящее удаление, а не архивирование."""
    session = _get_session_or_404(db, session_id)
    profile = _require_profile(session.EntityType)
    _require_write_access(profile, db, user)
    db.query(ImportRow).filter(ImportRow.ImportSessionId == session_id).delete()
    db.delete(session)
    db.commit()


@router.post("/sessions/cleanup")
def cleanup_sessions(
    db: DbSession,
    _user: Annotated[User, Depends(require_superadmin())],
    older_than_days: int = 60,
) -> dict:
    """Массовая очистка истории импортов старше N дней — таблица иначе растёт
    неограниченно. Затрагивает сессии любой сущности разом, поэтому право —
    ROLES.MANAGE (то же, что и остальные общесистемные действия), а не
    IMPORT конкретного модуля."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
    old_ids = list(
        db.scalars(
            select(ImportSession.Id).where(ImportSession.CreatedDate < cutoff)
        )
    )
    if old_ids:
        db.query(ImportRow).filter(ImportRow.ImportSessionId.in_(old_ids)).delete(
            synchronize_session=False
        )
        db.query(ImportSession).filter(ImportSession.Id.in_(old_ids)).delete(
            synchronize_session=False
        )
        db.commit()
    return {"deleted": len(old_ids)}
