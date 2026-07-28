import secrets
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession, require_roles
from app.core.security import hash_password
from app.models.enums import AccessRequestStatus, AuditAction, RoleCode
from app.models.user import AccessRequest, User, UserOrgAccess
from app.schemas.access_request import (
    AccessRequestCreate,
    AccessRequestDecision,
    AccessRequestOut,
)
from app.schemas.common import Page
from app.services.audit import log_action

router = APIRouter(prefix="/access-requests", tags=["access-requests"])


@router.post("", response_model=AccessRequestOut, status_code=status.HTTP_201_CREATED)
def submit_access_request(data: AccessRequestCreate, db: DbSession) -> AccessRequest:
    """Публичный эндпойнт: форма заявки на доступ, авторизация не требуется —
    у заявителя ещё нет учётной записи (Тома 1А §17 / План Sheets Dashboard §4).
    """
    obj = AccessRequest(**data.model_dump())
    db.add(obj)
    db.flush()
    log_action(
        db,
        table_name="AccessRequests",
        record_id=obj.Id,
        action=AuditAction.CREATE,
        user_id=None,
    )
    db.commit()
    db.refresh(obj)
    return obj


@router.get("", response_model=Page[AccessRequestOut])
def list_access_requests(
    db: DbSession,
    _user: Annotated[User, Depends(require_roles(RoleCode.ADMIN))],
    status_filter: AccessRequestStatus | None = None,
    skip: int = 0,
    limit: int = 50,
):
    query = select(AccessRequest)
    if status_filter is not None:
        query = query.where(AccessRequest.Status == status_filter)
    rows = db.scalars(query.offset(skip).limit(limit)).all()
    total = len(db.scalars(query).all())
    return Page(items=list(rows), total=total, skip=skip, limit=limit)


@router.post("/{request_id}/decide", response_model=AccessRequestOut)
def decide_access_request(
    request_id: uuid.UUID,
    decision: AccessRequestDecision,
    db: DbSession,
    admin: Annotated[User, Depends(require_roles(RoleCode.ADMIN))],
) -> AccessRequest:
    req = db.get(AccessRequest, request_id)
    if req is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Заявка не найдена")
    if req.Status != AccessRequestStatus.PENDING:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Заявка уже обработана")

    if not decision.Approve:
        req.Status = AccessRequestStatus.REJECTED
        req.DecidedByUserId = admin.Id
        log_action(
            db,
            table_name="AccessRequests",
            record_id=req.Id,
            action=AuditAction.UPDATE,
            user_id=admin.Id,
            field_name="Status",
            new_value=AccessRequestStatus.REJECTED.value,
        )
        db.commit()
        db.refresh(req)
        return req

    login = decision.Login or req.Email.split("@")[0]
    if db.scalar(select(User).where(User.Login == login)):
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Логин '{login}' уже занят, укажите другой"
        )
    temp_password = decision.TemporaryPassword or secrets.token_urlsafe(9)

    new_user = User(
        Login=login,
        Email=req.Email,
        HashedPassword=hash_password(temp_password),
        RoleId=req.RequestedRoleId,
        CreatedBy=admin.Id,
        ModifiedBy=admin.Id,
    )
    db.add(new_user)
    db.flush()

    if req.RequestedOrgUnitId is not None:
        db.add(
            UserOrgAccess(
                UserId=new_user.Id,
                OrgUnitId=req.RequestedOrgUnitId,
                CreatedBy=admin.Id,
                ModifiedBy=admin.Id,
            )
        )

    req.Status = AccessRequestStatus.APPROVED
    req.DecidedByUserId = admin.Id
    req.CreatedUserId = new_user.Id

    log_action(
        db,
        table_name="Users",
        record_id=new_user.Id,
        action=AuditAction.CREATE,
        user_id=admin.Id,
        new_value=f"created from AccessRequest {req.Id}",
    )
    db.commit()
    db.refresh(req)
    # Temporary password is returned once via Comment so the admin can relay
    # it to the new user; it is never stored in plain text.
    req.Comment = f"Логин: {login} / Временный пароль: {temp_password}"
    return req
