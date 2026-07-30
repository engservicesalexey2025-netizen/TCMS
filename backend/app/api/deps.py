import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token_payload
from app.models.security import UserSession
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession, token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить учётные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token_payload(token)
    if payload is None or payload.get("mfa_pending"):
        raise credentials_error

    sub = payload.get("sub")
    try:
        actor_id = uuid.UUID(sub) if sub else None
    except ValueError:
        actor_id = None
    if actor_id is None:
        raise credentials_error

    jti = payload.get("jti")
    if jti:
        session = db.get(UserSession, uuid.UUID(jti))
        now = datetime.now(timezone.utc)
        if (
            session is None
            or session.RevokedAt is not None
            or session.ExpiresAt <= now
        ):
            raise credentials_error

    actor = db.get(User, actor_id)
    if actor is None or not actor.IsActive:
        raise credentials_error
    if jti:
        actor._current_jti = uuid.UUID(jti)

    acting_as = payload.get("acting_as")
    if not acting_as:
        return actor

    target = db.get(User, uuid.UUID(acting_as))
    if target is None or not target.IsActive:
        raise credentials_error
    # «Просмотреть как пользователь» (доп. рекомендация №4 ТЗ): права/данные
    # считаются от имени target, но кто фактически действует — видно через
    # эти атрибуты (используются require_permission, /auth/me и аудитом).
    if jti:
        target._current_jti = uuid.UUID(jti)
    target._view_as_actor_id = actor.Id
    target._is_view_as = True
    return target


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_permission(module: str, action: str):
    """Центральная проверка прав (модуль 001 «Управление доступом и
    безопасностью») — заменяет require_roles() в бизнес-роутерах. Смотрит
    RolePermissions/UserPermissions/Delegations через
    app.services.permissions.user_has_permission, а не одну плоскую роль."""

    def dependency(db: DbSession, user: CurrentUser) -> User:
        from app.services.permissions import user_has_permission

        if action != "VIEW" and getattr(user, "_is_view_as", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Режим «Просмотреть как пользователь» доступен только для чтения",
            )
        if not user_has_permission(db, user, module, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для этого действия",
            )
        return user

    return dependency


def require_superadmin():
    """Управление ролями/правами (Конструктор, §16 ТЗ) защищено отдельно от
    гранулярных прав — иначе админ рискует случайно отобрать у себя же
    доступ к экрану, которым это чинится."""
    return require_permission("ROLES", "MANAGE")
