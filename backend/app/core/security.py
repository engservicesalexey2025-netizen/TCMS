import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def generate_temporary_password() -> str:
    """Временный пароль вида P8!gK41#Lm (§6 ТЗ)."""
    alphabet = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789"
    body = "".join(secrets.choice(alphabet) for _ in range(8))
    return f"{secrets.choice('!#$%')}{body}{secrets.choice('!#$%')}"


def check_password_strength(password: str) -> str | None:
    """Возвращает текст ошибки или None, если пароль проходит проверку
    (§8 ТЗ: длина; сложность)."""
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return f"Пароль должен содержать не менее {settings.PASSWORD_MIN_LENGTH} символов"
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    if not (has_letter and has_digit):
        return "Пароль должен содержать буквы и цифры"
    return None


def create_access_token(
    user_id: UUID,
    *,
    jti: UUID | None = None,
    expires_minutes: int | None = None,
    acting_as: UUID | None = None,
    mfa_pending: bool = False,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict = {"sub": str(user_id), "exp": expire}
    if jti is not None:
        payload["jti"] = str(jti)
    if acting_as is not None:
        payload["acting_as"] = str(acting_as)
    if mfa_pending:
        payload["mfa_pending"] = True
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token_payload(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


def generate_reset_token() -> tuple[str, str]:
    """Возвращает (сырой токен для ссылки, его хеш для хранения в БД)."""
    raw = secrets.token_urlsafe(32)
    return raw, hash_reset_token(raw)


def hash_reset_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
