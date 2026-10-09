import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.enums import (
    ImportRowAppliedAction,
    ImportRowClassification,
    ImportRowDecision,
    ImportSessionStatus,
)


class ImportSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: uuid.UUID
    EntityType: str
    FileName: str
    Status: ImportSessionStatus
    CreatedBy: uuid.UUID | None
    CreatedDate: datetime
    AppliedBy: uuid.UUID | None
    AppliedDate: datetime | None
    ErrorMessage: str | None
    Counts: dict[str, int] = {}
    Columns: list[dict[str, Any]] = []


class ImportRowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: uuid.UUID
    RowNumber: int
    RawData: dict[str, Any]
    NormalizedData: dict[str, Any] | None
    MatchedRecordId: uuid.UUID | None
    Classification: ImportRowClassification
    DiffFields: dict[str, Any] | None
    ValidationError: str | None
    Decision: ImportRowDecision
    AppliedAction: ImportRowAppliedAction | None
    AppliedError: str | None


class RowDecisionUpdate(BaseModel):
    decision: ImportRowDecision


class RowDataUpdate(BaseModel):
    data: dict[str, Any]


class BulkRowDecisionUpdate(BaseModel):
    decision: ImportRowDecision
    row_ids: list[uuid.UUID] | None = None
    classification: ImportRowClassification | None = None


class ApplyResult(BaseModel):
    created: int
    updated: int
    failed: int
    skipped: int
    remaining_pending: int
