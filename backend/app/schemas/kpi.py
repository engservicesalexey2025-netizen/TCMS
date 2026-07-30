from app.models.enums import KpiMetricType, ObjectCategory, SupervisionStage
from app.schemas.common import AuditFields
from pydantic import BaseModel


class KpiNormMatrixOut(AuditFields):
    ObjectCategory: ObjectCategory
    Stage: SupervisionStage
    MetricType: KpiMetricType
    NormValue: int


class KpiNormMatrixUpdate(BaseModel):
    NormValue: int


class KpiSettingsOut(AuditFields):
    WeightKpi: float
    WeightIqc: float
    WeightCri: float
    WeightS1: float
    WeightS2: float
    WeightS3: float
    WeightS4: float
    WeightDiversity: float
    WeightNormative: float
    WeightTechnical: float
    CriTarget: float
    CategoryExcellentMin: float
    CategoryGoodMin: float
    CategorySatisfactoryMin: float


class KpiSettingsUpdate(BaseModel):
    WeightKpi: float | None = None
    WeightIqc: float | None = None
    WeightCri: float | None = None
    WeightS1: float | None = None
    WeightS2: float | None = None
    WeightS3: float | None = None
    WeightS4: float | None = None
    WeightDiversity: float | None = None
    WeightNormative: float | None = None
    WeightTechnical: float | None = None
    CriTarget: float | None = None
    CategoryExcellentMin: float | None = None
    CategoryGoodMin: float | None = None
    CategorySatisfactoryMin: float | None = None
