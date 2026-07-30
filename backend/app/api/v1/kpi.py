import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession, require_permission
from app.models.kpi import KpiNormMatrix, KpiSettings
from app.models.user import User
from app.schemas.kpi import (
    KpiNormMatrixOut,
    KpiNormMatrixUpdate,
    KpiSettingsOut,
    KpiSettingsUpdate,
)
from app.services.crud_base import AuditedRepository

router = APIRouter(prefix="/kpi", tags=["kpi"])

matrix_repo = AuditedRepository(KpiNormMatrix)
settings_repo = AuditedRepository(KpiSettings)

MatrixViewUser = Annotated[User, Depends(require_permission("KPI", "VIEW"))]
MatrixWriteUser = Annotated[User, Depends(require_permission("KPI", "UPDATE"))]
SettingsViewUser = Annotated[User, Depends(require_permission("KPI_SETTINGS", "VIEW"))]
SettingsWriteUser = Annotated[User, Depends(require_permission("KPI_SETTINGS", "UPDATE"))]


@router.get("/norm-matrix", response_model=list[KpiNormMatrixOut])
def list_norm_matrix(db: DbSession, _user: MatrixViewUser):
    """Полный список из 60 фиксированных ячеек (5 типов × 6 стадий × 2
    метрики) — без пагинации, набор строк не меняется, редактируется только
    NormValue."""
    rows = db.scalars(
        select(KpiNormMatrix).order_by(
            KpiNormMatrix.MetricType, KpiNormMatrix.Stage, KpiNormMatrix.ObjectCategory
        )
    ).all()
    return rows


@router.patch("/norm-matrix/{item_id}", response_model=KpiNormMatrixOut)
def update_norm_matrix_cell(
    item_id: uuid.UUID, data: KpiNormMatrixUpdate, db: DbSession, user: MatrixWriteUser
):
    obj = matrix_repo.update(db, item_id, data.model_dump(exclude_unset=True), user.Id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
    return obj


def _get_settings_or_404(db) -> KpiSettings:
    obj = db.scalar(select(KpiSettings).limit(1))
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Коэффициенты не настроены")
    return obj


@router.get("/settings", response_model=KpiSettingsOut)
def get_settings(db: DbSession, _user: SettingsViewUser):
    return _get_settings_or_404(db)


@router.patch("/settings", response_model=KpiSettingsOut)
def update_settings(data: KpiSettingsUpdate, db: DbSession, user: SettingsWriteUser):
    current = _get_settings_or_404(db)
    obj = settings_repo.update(db, current.Id, data.model_dump(exclude_unset=True), user.Id)
    return obj
