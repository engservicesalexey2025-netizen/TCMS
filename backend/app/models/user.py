import uuid

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin
from app.models.enums import AccessRequestStatus, RoleCode


class Role(Base, AuditMixin):
    """Справочник ролей. Иерархия доступа фиксирована на уровне бизнес-логики,
    не на уровне структуры таблицы (§2 Тома 1А — карточка/справочник, не код).
    """

    __tablename__ = "Roles"

    Code: Mapped[RoleCode] = mapped_column(
        Enum(RoleCode, name="role_code"), nullable=False, unique=True
    )
    Name: Mapped[str] = mapped_column(String(255), nullable=False)


class User(Base, AuditMixin):
    __tablename__ = "Users"

    Login: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    Email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    HashedPassword: Mapped[str] = mapped_column(String(255), nullable=False)
    RoleId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Roles.Id"), nullable=False
    )
    EmployeeId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Employees.Id"), nullable=True
    )

    Role: Mapped["Role"] = relationship(foreign_keys=[RoleId])


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


class AccessRequest(Base, AuditMixin):
    """Заявка на доступ: форма → одобряет Admin → автоматически создаётся
    User + UserOrgAccess с указанной ролью/оргединицей.
    """

    __tablename__ = "AccessRequests"

    FullName: Mapped[str] = mapped_column(String(255), nullable=False)
    Email: Mapped[str] = mapped_column(String(255), nullable=False)
    RequestedRoleId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Roles.Id"), nullable=False
    )
    RequestedOrgUnitId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("OrgUnits.Id"), nullable=True
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
