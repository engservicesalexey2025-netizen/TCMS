import enum


class OrgUnitType(str, enum.Enum):
    DIVISION = "DIVISION"  # Дивизион
    DEPARTMENT = "DEPARTMENT"  # Управление
    GROUP = "GROUP"  # Группа


class RoleCode(str, enum.Enum):
    ADMIN = "ADMIN"
    DIVISION_DIRECTOR = "DIVISION_DIRECTOR"
    DEPARTMENT_HEAD = "DEPARTMENT_HEAD"
    GROUP_HEAD = "GROUP_HEAD"
    OBSERVER = "OBSERVER"


class AccessRequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class EmployeeStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ON_LEAVE = "ON_LEAVE"
    DISMISSED = "DISMISSED"


class Gender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class ProjectStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SUSPENDED = "SUSPENDED"


class RemarkStatus(str, enum.Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"


class AuditAction(str, enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    ARCHIVE = "ARCHIVE"
    RESTORE = "RESTORE"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    DELETE = "DELETE"


class ImportSessionStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    VALIDATED = "VALIDATED"
    REVIEW = "REVIEW"
    APPLYING = "APPLYING"
    APPLIED = "APPLIED"
    PARTIALLY_APPLIED = "PARTIALLY_APPLIED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ImportRowClassification(str, enum.Enum):
    NEW = "NEW"
    IDENTICAL = "IDENTICAL"
    CONFLICT = "CONFLICT"
    AMBIGUOUS = "AMBIGUOUS"
    ERROR = "ERROR"


class ImportRowDecision(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"


class ImportRowAppliedAction(str, enum.Enum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"
