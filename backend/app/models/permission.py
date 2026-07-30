"""Модуль «Управление доступом и безопасностью»: каталог прав (RBAC),
колоночная (Column-Level) и построчная (Row-Level / DataScope) безопасность,
делегирование полномочий.

`Module`/`Action`/`ScopeType`/`Mode` — обычные VARCHAR, не Postgres ENUM:
новый модуль/роль/область видимости должны появляться через административный
интерфейс («Конструктор прав доступа», §16 ТЗ) без миграции схемы.
"""
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin


class Permission(Base, AuditMixin):
    """Каталог прав: одна строка = одна бизнес-функция (Модуль + Действие),
    напр. (EMPLOYEES, EXPORT). Права по разделам/модулям из ТЗ — это проекция
    этой же таблицы, а не отдельное хранилище (см. план, §2)."""

    __tablename__ = "Permissions"
    __table_args__ = (UniqueConstraint("Module", "Action"),)

    Module: Mapped[str] = mapped_column(String(50), nullable=False)
    Action: Mapped[str] = mapped_column(String(20), nullable=False)
    Code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    Name: Mapped[str] = mapped_column(String(255), nullable=False)


class RolePermission(Base, AuditMixin):
    """Наличие активной (IsActive) строки = роль обладает правом. Отзыв права
    у роли — обычная архивация, как везде в проекте."""

    __tablename__ = "RolePermissions"
    __table_args__ = (UniqueConstraint("RoleId", "PermissionId"),)

    RoleId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Roles.Id"), nullable=False
    )
    PermissionId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Permissions.Id"), nullable=False
    )


class UserPermission(Base, AuditMixin):
    """Индивидуальное исключение из роли — «если требуется исключение из
    роли» (§18 ТЗ). DENY побеждает всё, GRANT добавляет то, чего нет у ролей
    пользователя. ExpiresAt — точечный временный доступ (напр. аудитору)."""

    __tablename__ = "UserPermissions"
    __table_args__ = (UniqueConstraint("UserId", "PermissionId"),)

    UserId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=False
    )
    PermissionId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Permissions.Id"), nullable=False
    )
    Effect: Mapped[str] = mapped_column(String(6), nullable=False)  # GRANT | DENY
    ExpiresAt: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    Reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class UserRole(Base, AuditMixin):
    """Многие-ко-многим User↔Role, заменяет прежний единичный User.RoleId.
    ExpiresAt — временный доступ (доп. рекомендация №2 ТЗ)."""

    __tablename__ = "UserRoles"
    __table_args__ = (UniqueConstraint("UserId", "RoleId"),)

    UserId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=False
    )
    RoleId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Roles.Id"), nullable=False
    )
    ExpiresAt: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class ColumnPermission(Base, AuditMixin):
    """Права по столбцам (§14 ТЗ). Ровно одно из RoleId/UserId заполнено —
    персональное правило (UserId) всегда побеждает ролевое. Три режима вместо
    boolean, чтобы точно воспроизвести сегодняшнее поведение masking.py:
    FULL (по умолчанию, нет строки) — видно как есть; MASKED — частично
    (как сейчас ИИН, ********1234); HIDDEN — не показывается вовсе
    (как сейчас PersonalPhone)."""

    __tablename__ = "ColumnPermissions"
    __table_args__ = (
        CheckConstraint(
            '("RoleId" IS NOT NULL) <> ("UserId" IS NOT NULL)',
            name="ck_column_permissions_role_xor_user",
        ),
    )

    EntityName: Mapped[str] = mapped_column(String(100), nullable=False)
    FieldName: Mapped[str] = mapped_column(String(100), nullable=False)
    RoleId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Roles.Id"), nullable=True
    )
    UserId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=True
    )
    Mode: Mapped[str] = mapped_column(String(10), nullable=False)  # FULL | MASKED | HIDDEN


class DataScope(Base, AuditMixin):
    """Ограничение по данным (§15 ТЗ) — ручное исключение СВЕРХ двух уже
    существующих источников RLS: UserOrgAccess (организации) и Assignments
    (проекты через назначение сотрудника). ScopeId — полиморфная ссылка без
    FK (может указывать на Projects/Contractors/... в зависимости от
    ScopeType), т.к. один столбец не может ссылаться на разные таблицы."""

    __tablename__ = "DataScopes"
    __table_args__ = (UniqueConstraint("UserId", "ScopeType", "ScopeId"),)

    UserId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=False
    )
    ScopeType: Mapped[str] = mapped_column(String(20), nullable=False)  # PROJECT | CONTRACTOR | ...
    ScopeId: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    ExpiresAt: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    GrantedByUserId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=True
    )
    Reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class Delegation(Base, AuditMixin):
    """Делегирование полномочий (доп. рекомендация №3 ТЗ): руководитель
    временно передаёт свои права заместителю. RoleId=NULL означает «все роли
    FromUser». Намеренно не транзитивно — проверяется только прямой
    FromUserId, без обхода цепочек (исключает эскалацию привилегий)."""

    __tablename__ = "Delegations"

    FromUserId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=False
    )
    ToUserId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=False
    )
    RoleId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Roles.Id"), nullable=True
    )
    StartsAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ExpiresAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    Reason: Mapped[str | None] = mapped_column(Text, nullable=True)
