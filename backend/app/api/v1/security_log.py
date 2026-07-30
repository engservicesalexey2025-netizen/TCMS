"""Журнал безопасности (§17 ТЗ): вход/неудачный вход (LoginHistory) +
чувствительные события из общего AuditLog (смена пароля, роли, права,
выдача полного доступа, создание пользователя, просмотр как пользователь,
экспорт). Объединяется в Python, а не SQL UNION — источники слишком разной
формы (разные колонки), а объём событий пока не требует UNION на уровне БД.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.deps import DbSession, require_permission
from app.models.audit import AuditLog
from app.models.enums import AuditAction
from app.models.security import LoginHistory
from app.models.user import User
from app.schemas.common import Page
from app.schemas.security_log import SecurityLogEntryOut

router = APIRouter(prefix="/security-log", tags=["security-log"])

_SENSITIVE_TABLES = {"Users", "Roles", "RolePermissions", "UserPermissions", "UserRoles", "ColumnPermissions"}

_ACTION_LABELS = {
    "HashedPassword": "PASSWORD_CHANGE",
    "MfaEnabled": "MFA_CHANGE",
}


@router.get("", response_model=Page[SecurityLogEntryOut])
def list_security_log(
    db: DbSession,
    _user: User = Depends(require_permission("SECURITY_LOG", "VIEW")),
    skip: int = 0,
    limit: int = 50,
) -> Page:
    entries: list[SecurityLogEntryOut] = []

    logins = db.execute(
        select(LoginHistory, User.Login)
        .join(User, User.Id == LoginHistory.UserId, isouter=True)
    ).all()
    for row, login in logins:
        entries.append(
            SecurityLogEntryOut(
                Id=row.Id,
                OccurredAt=row.CreatedDate,
                UserId=row.UserId,
                UserLogin=login or row.LoginAttempted,
                Action="LOGIN",
                Result="SUCCESS" if row.Success else "FAILURE",
                IpAddress=row.IpAddress,
                UserAgent=row.UserAgent,
                Detail=row.Reason,
            )
        )

    audit_rows = db.execute(
        select(AuditLog, User.Login)
        .join(User, User.Id == AuditLog.ChangedByUserId, isouter=True)
        .where(AuditLog.TableName.in_(_SENSITIVE_TABLES))
    ).all()
    for row, login in audit_rows:
        action_label = _ACTION_LABELS.get(row.FieldName) if row.FieldName else None
        if action_label is None:
            action_label = row.Action.value if row.Action == AuditAction.VIEW_AS else f"{row.TableName}_{row.Action.value}"
        entries.append(
            SecurityLogEntryOut(
                Id=row.Id,
                OccurredAt=row.ChangedDate,
                UserId=row.ChangedByUserId,
                UserLogin=login,
                Action=action_label,
                Result="SUCCESS",
                IpAddress=row.IpAddress,
                Detail=row.Reason,
            )
        )

    entries.sort(key=lambda e: e.OccurredAt, reverse=True)
    total = len(entries)
    return Page(items=entries[skip : skip + limit], total=total, skip=skip, limit=limit)
