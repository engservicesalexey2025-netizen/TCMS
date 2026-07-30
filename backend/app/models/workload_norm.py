from sqlalchemy import Enum, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin
from app.models.enums import WorkloadCategory


class AdditionalWorkloadNorm(Base, AuditMixin):
    """Норма дополнительной нагрузки по категории (регламент BIG-HRM-RGL-038-RU,
    Таблица 1 и Разделы 4.1–4.2) — используется для расчёта ежеквартальной
    надбавки за объёмы работ сверх нормы. Строки фиксированы (10 категорий),
    заполняются миграцией; редактируются только числовые значения и ссылка
    на внешнюю метрику. SignalValue/Coefficient/MetricLinkUrl не применимы ко
    всем категориям (например, у руководителей групп/управлений в регламенте
    нет явного коэффициента — расчёт там ведётся по внешней BI-таблице),
    поэтому эти поля nullable.
    """

    __tablename__ = "AdditionalWorkloadNorms"

    Category: Mapped[WorkloadCategory] = mapped_column(
        Enum(WorkloadCategory, name="workload_category"), nullable=False, unique=True
    )
    NormValue: Mapped[int] = mapped_column(Integer, nullable=False)  # Норма, м2
    SignalValue: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Сигнал к привлечению помощника/доп. ТН, м2
    LimitValue: Mapped[int] = mapped_column(Integer, nullable=False)  # Предел, выше которого расчёт не производится, м2
    Coefficient: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)  # Коэффициент надбавки
    MetricLinkUrl: Mapped[str | None] = mapped_column(String(1000), nullable=True)  # Ссылка на расчёт метрики (внешний BI)
