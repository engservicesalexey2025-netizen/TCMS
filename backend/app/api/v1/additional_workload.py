import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession, require_permission
from app.models.user import User
from app.models.workload_norm import AdditionalWorkloadNorm
from app.schemas.workload_norm import WorkloadNormOut, WorkloadNormUpdate
from app.services.crud_base import AuditedRepository

router = APIRouter(prefix="/workload-norms", tags=["workload-norms"])

repo = AuditedRepository(AdditionalWorkloadNorm)

ViewUser = Annotated[User, Depends(require_permission("WORKLOAD_NORMS", "VIEW"))]
WriteUser = Annotated[User, Depends(require_permission("WORKLOAD_NORMS", "UPDATE"))]


@router.get("", response_model=list[WorkloadNormOut])
def list_workload_norms(db: DbSession, _user: ViewUser):
    """Полный список из 10 фиксированных категорий (регламент BIG-HRM-RGL-038-RU)
    — без пагинации, набор строк не меняется, редактируются только значения."""
    return db.scalars(select(AdditionalWorkloadNorm).order_by(AdditionalWorkloadNorm.Category)).all()


@router.patch("/{item_id}", response_model=WorkloadNormOut)
def update_workload_norm(
    item_id: uuid.UUID, data: WorkloadNormUpdate, db: DbSession, user: WriteUser
):
    obj = repo.update(db, item_id, data.model_dump(exclude_unset=True), user.Id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
    return obj
