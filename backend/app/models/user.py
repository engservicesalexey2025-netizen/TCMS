import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin
from app.models.enums import AccessRequestStatus


class Role(Base, AuditMixin):
    """Справочник ролей. Иерархия доступа фиксирована на уровне бизнес-логики,
    не на уровне структуры таблицы (§2 Тома 1А — карточка/справочник, не код).

    `Code` — VARCHAR, не Postgres ENUM: новые роли (Лаборатория/Подрядчик/
    Заказчик и т.д.) создаются администратором через «Конструктор прав
    доступа» без миграции схемы (см. RoleCode в app/models/enums.py — теперь
    это только набор именованных констант для сидов, не ограничение БД).
    """

    __tablename__ = "Roles"

    Code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    Name: Mapped[str] = mapped_column(String(255), nullable=False)
    BypassDataScope: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Видит все строки без RLS-фильтрации"
    )
    IsSystem: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Защищена от удаления/переименования в конструкторе"
    )


class User(Base, AuditMixin):
    __tablename__ = "Users"

    Login: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    Email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    HashedPassword: Mapped[str] = mapped_column(String(255), nullable=False)
    EmployeeId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Employees.Id"), nullable=True
    )

    FailedLoginAttempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    LockedUntil: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    LastLoginAt: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    LastLoginIp: Mapped[str | None] = mapped_column(String(45), nullable=True)
    PasswordChangedAt: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    MustChangePassword: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    MfaEnabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    MfaSecret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    MfaRecoveryCodesHash: Mapped[str | None] = mapped_column(Text, nullable=True)


class UserOrgAccess(Base, AuditMixin):
    """Доступ пользователя к оргединице. Многие-ко-многим: один Наблюдатель
    может быть назначен на несколько Управлений/Групп (см. План Sheets
    Dashboard §4) — для DepartmentHead/GroupHead здесь будет ровно одна запись.
    """

    __tablename__ = "UserOrgAccess"
    __table_args__ = (UniqueConstraint("UserId", "OrgUnitId"),)

    UserId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=False
    )
    OrgUnitId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("OrgUnits.Id"), nullable=False
    )
    ExpiresAt: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AccessRequest(Base, AuditMixin):
    """Заявка на доступ: форма → одобряет Admin → автоматически создаётся
    User + UserOrgAccess с указанной ролью/оргединицей.
    """

    __tablename__ = "AccessRequests"

    FullName: Mapped[str] = mapped_column(String(255), nullable=False)
    Email: Mapped[str] = mapped_column(String(255), nullable=False)
    Phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    Organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    Position: Mapped[str | None] = mapped_column(String(255), nullable=True)
    RequestedRoleId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Roles.Id"), nullable=False
    )
    RequestedOrgUnitId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("OrgUnits.Id"), nullable=True
    )
    RequestedProjectId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Projects.Id"), nullable=True
    )
    Status: Mapped[AccessRequestStatus] = mapped_column(
        Enum(AccessRequestStatus, name="access_request_status"),
        default=AccessRequestStatus.PENDING,
        nullable=False,
    )
    DecidedByUserId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=True
    )
    CreatedUserId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=True
    )
