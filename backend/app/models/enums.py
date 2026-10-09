import enum


class OrgUnitType(str, enum.Enum):
    DIVISION = "DIVISION"  # Дивизион — верхний уровень
    CITY = "CITY"  # Город (филиал) — во главе Директор филиала
    DEPARTMENT = "DEPARTMENT"  # Управление — во главе Руководитель управления
    GROUP = "GROUP"  # Группа — во главе Руководитель группы


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
    VIEW_AS = "VIEW_AS"


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


class ObjectCategory(str, enum.Enum):
    """Тип объекта — фиксированная таксономия матриц норм KPI (Раздел 6
    методики оценки эффективности), отличная от свободного справочника
    ProjectType на вкладке Проекты: значения здесь жёстко заданы, потому что
    на них ссылаются строки норм-матрицы."""

    RESIDENTIAL = "RESIDENTIAL"  # Жилое
    PUBLIC = "PUBLIC"  # Общественное
    INDUSTRIAL = "INDUSTRIAL"  # Промышленное
    LINEAR = "LINEAR"  # Линейный
    UTILITY_NETWORKS = "UTILITY_NETWORKS"  # Инженерные сети


class SupervisionStage(str, enum.Enum):
    """Стадия для матриц норм KPI (Раздел 6) — фиксированный список из шести
    стадий строительного контроля, не путать со свободным справочником
    ProjectStage на вкладке Проекты."""

    EARTHWORKS = "EARTHWORKS"  # Земляные работы / нулевой цикл
    MONOLITH_FRAME = "MONOLITH_FRAME"  # Монолит / каркас
    FACADE_ROOF = "FACADE_ROOF"  # Фасад и кровля
    MEP = "MEP"  # Инженерные сети (МЭП)
    FINISHING = "FINISHING"  # Отделочные работы
    COMMISSIONING = "COMMISSIONING"  # Пусконаладка / сдача


class KpiMetricType(str, enum.Enum):
    PRESCRIPTIONS = "PRESCRIPTIONS"  # Норма предписаний (компонент S1)
    INSPECTIONS = "INSPECTIONS"  # Норма инспекций (компонент S3)


class WorkloadCategory(str, enum.Enum):
    """Фиксированные категории норм из регламента BIG-HRM-RGL-038-RU
    «Начисление ежеквартальных выплат за дополнительные объемы работ ТН»
    (Таблица 1, Разделы 4.1–4.2)."""

    GENERAL_CONSTRUCTION_ENGINEER = "GENERAL_CONSTRUCTION_ENGINEER"  # Инженер ТН по общестроительным работам
    UTILITY_NETWORKS_ENGINEER = "UTILITY_NETWORKS_ENGINEER"  # Инженер ТН по инженерным сетям
    GROUP_DIVISION_HEAD_ON_SITE_CENTER = "GROUP_DIVISION_HEAD_ON_SITE_CENTER"  # РГ, РУ на объектах (Ц-З, Ц-С)
    GROUP_HEAD_K2_CENTER = "GROUP_HEAD_K2_CENTER"  # РГ K2 BI / K2+ фасады либо геодезия (Ц-З, Ц-С)
    GROUP_DIVISION_HEAD_EXTERNAL_CENTER = "GROUP_DIVISION_HEAD_EXTERNAL_CENTER"  # РГ, РУ на внешних проектах, доля ≥50% (Ц-З, Ц-С)
    BRANCH_DIRECTOR_K2_CENTER = "BRANCH_DIRECTOR_K2_CENTER"  # ДФ (К2) (Ц-З, Ц-С)
    BRANCH_DIRECTOR_K2_EXTERNAL_CENTER = "BRANCH_DIRECTOR_K2_EXTERNAL_CENTER"  # ДФ (К2+Внешние) (Ц-З, Ц-С)
    GROUP_HEAD_ALMATY_SHYMKENT = "GROUP_HEAD_ALMATY_SHYMKENT"  # РГ (Алматы, Шымкент)
    DIVISION_HEAD_ALMATY_SHYMKENT = "DIVISION_HEAD_ALMATY_SHYMKENT"  # РУ (Алматы, Шымкент)
    BRANCH_DIRECTOR_ALMATY_SHYMKENT = "BRANCH_DIRECTOR_ALMATY_SHYMKENT"  # ДФ (Алматы, Шымкент)
