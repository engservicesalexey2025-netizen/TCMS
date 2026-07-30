from sqlalchemy import Enum, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin
from app.models.enums import KpiMetricType, ObjectCategory, SupervisionStage


class KpiNormMatrix(Base, AuditMixin):
    """Норма предписаний/инспекций по паре «тип объекта × стадия» (Раздел 6
    методики оценки эффективности технадзора) — используется в компонентах
    S1 (норма предписаний) и S3 (норма инспекций) блока KPI. Строки
    фиксированы (5 типов × 6 стадий × 2 метрики = 60), редактируется только
    NormValue; таблица заполняется миграцией, добавление/удаление строк
    через API не предусмотрено.
    """

    __tablename__ = "KpiNormMatrix"
    __table_args__ = (
        UniqueConstraint("ObjectCategory", "Stage", "MetricType", name="uq_KpiNormMatrix_cell"),
    )

    ObjectCategory: Mapped[ObjectCategory] = mapped_column(
        Enum(ObjectCategory, name="kpi_object_category"), nullable=False
    )
    Stage: Mapped[SupervisionStage] = mapped_column(
        Enum(SupervisionStage, name="kpi_supervision_stage"), nullable=False
    )
    MetricType: Mapped[KpiMetricType] = mapped_column(
        Enum(KpiMetricType, name="kpi_metric_type"), nullable=False
    )
    NormValue: Mapped[int] = mapped_column(Integer, nullable=False)


class KpiSettings(Base, AuditMixin):
    """Единственная строка глобальных коэффициентов методики (Разделы 1–5):
    веса блоков ИТОГ, веса компонентов KPI/IQC, целевой CRI и границы
    категорий. API всегда читает/обновляет первую (и единственную) строку;
    таблица заполняется миграцией с значениями по умолчанию из регламента.
    """

    __tablename__ = "KpiSettings"

    # ИТОГ = WeightKpi*KPI + WeightIqc*IQC + WeightCri*CRI-балл (Раздел 1)
    WeightKpi: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.50)
    WeightIqc: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.35)
    WeightCri: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.15)

    # KPI = WeightS1*S1 + WeightS2*S2 + WeightS3*S3 + WeightS4*S4 (Раздел 2)
    WeightS1: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.30)
    WeightS2: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.20)
    WeightS3: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.20)
    WeightS4: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.30)

    # IQC = WeightDiversity*Diversity + WeightNormative*Normative + WeightTechnical*Technical (Раздел 3)
    WeightDiversity: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False, default=0.2857)
    WeightNormative: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False, default=0.4286)
    WeightTechnical: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False, default=0.2857)

    # CRI-балл = МИН(CRI / CriTarget; 1) × 100 (Раздел 4)
    CriTarget: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.30)

    # Границы категорий по ИТОГ (Раздел 5) — нижняя граница каждой категории.
    CategoryExcellentMin: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=85)
    CategoryGoodMin: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=70)
    CategorySatisfactoryMin: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=55)
