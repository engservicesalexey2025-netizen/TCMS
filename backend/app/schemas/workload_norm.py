from app.models.enums import WorkloadCategory
from app.schemas.common import AuditFields
from pydantic import BaseModel


class WorkloadNormOut(AuditFields):
    Category: WorkloadCategory
    NormValue: int
    SignalValue: int | None
    LimitValue: int
    Coefficient: float | None
    MetricLinkUrl: str | None


class WorkloadNormUpdate(BaseModel):
    NormValue: int | None = None
    SignalValue: int | None = None
    LimitValue: int | None = None
    Coefficient: float | None = None
    MetricLinkUrl: str | None = None
