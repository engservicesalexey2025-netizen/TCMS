"""Журналы и сессии модуля безопасности. Не бизнес-сущности — не используют
AuditMixin, по образцу AuditLog (app/models/audit.py): это сами по себе
журналы, а не данные, которые нужно архивировать/версионировать.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LoginHistory(Base):
    """Попытки входа — успешные и нет. UserId нулевой, если введённый логин
    вообще не существует. У события входа нет диффа полей, поэтому это не
    строка в AuditLog (см. план, §1.6)."""

    __tablename__ = "LoginHistory"

    Id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    UserId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=True
    )
    LoginAttempted: Mapped[str] = mapped_column(String(100), nullable=False)
    Success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    Reason: Mapped[str | None] = mapped_column(String(50), nullable=True)
    IpAddress: Mapped[str | None] = mapped_column(String(45), nullable=True)
    UserAgent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    CreatedDate: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PasswordHistory(Base):
    """Последние хеши паролей пользователя — проверка «не повторять последние
    N» при смене пароля (§8 ТЗ)."""

    __tablename__ = "PasswordHistory"

    Id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    UserId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=False
    )
    HashedPassword: Mapped[str] = mapped_column(String(255), nullable=False)
    CreatedDate: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UserSession(Base):
    """Серверно-отзываемая сессия — Id совпадает со значением claim `jti` в
    выданном JWT. Без этой таблицы отзыв конкретного устройства/принудительный
    logout при смене пароля физически невозможны (JWT сам по себе
    неотзываем)."""

    __tablename__ = "UserSessions"

    Id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    UserId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=False
    )
    IssuedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ExpiresAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    RevokedAt: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    IpAddress: Mapped[str | None] = mapped_column(String(45), nullable=True)
    UserAgent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ActingAsUserId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=True
    )


class PasswordResetToken(Base):
    """Одноразовая ссылка восстановления пароля (§9 ТЗ, 15 минут). Хранится
    хеш токена, не сырое значение — как HashedPassword у User."""

    __tablename__ = "PasswordResetTokens"

    Id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    UserId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=False
    )
    TokenHash: Mapped[str] = mapped_column(String(255), nullable=False)
    ExpiresAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    UsedAt: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    CreatedDate: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
