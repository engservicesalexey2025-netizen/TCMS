"""Вспомогательные функции для сессий/истории входов — общая логика, которую
использует и обычный логин, и «Просмотреть как пользователь» (§7/§8/§17 ТЗ).
"""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.models.security import LoginHistory, UserSession
from app.models.user import User


def record_login_attempt(
    db: Session,
    *,
    login_attempted: str,
    user: User | None,
    success: bool,
    reason: str | None,
    ip_address: str | None,
    user_agent: str | None,
) -> None:
    db.add(
        LoginHistory(
            UserId=user.Id if user else None,
            LoginAttempted=login_attempted,
            Success=success,
            Reason=reason,
            IpAddress=ip_address,
            UserAgent=user_agent,
        )
    )
    db.commit()


def issue_session_token(
    db: Session,
    user: User,
    *,
    ip_address: str | None = None,
    user_agent: str | None = None,
    acting_as: uuid.UUID | None = None,
    expires_minutes: int | None = None,
) -> str:
    """Создаёт строку UserSessions и выдаёт JWT с её Id в claim `jti` — без
    этого отзыв конкретного устройства/принудительный logout при смене
    пароля невозможны (JWT сам по себе неотзываем)."""
    jti = uuid.uuid4()
    expires = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires)
    db.add(
        UserSession(
            Id=jti,
            UserId=user.Id,
            ExpiresAt=expires_at,
            IpAddress=ip_address,
            UserAgent=user_agent,
            ActingAsUserId=acting_as,
        )
    )
    db.commit()
    return create_access_token(
        user.Id, jti=jti, expires_minutes=expires, acting_as=acting_as
    )


def revoke_other_sessions(db: Session, user: User, keep_jti: uuid.UUID | None) -> None:
    """Отзывает все сессии пользователя, кроме указанной — используется при
    смене пароля (§8 ТЗ: смена пароля должна завершать остальные сеансы)."""
    now = datetime.now(timezone.utc)
    sessions = db.query(UserSession).filter(
        UserSession.UserId == user.Id, UserSession.RevokedAt.is_(None)
    )
    for session in sessions:
        if keep_jti is not None and session.Id == keep_jti:
            continue
        session.RevokedAt = now
    db.commit()
