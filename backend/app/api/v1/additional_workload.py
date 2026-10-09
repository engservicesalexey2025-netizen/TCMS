import uuid
from io import BytesIO
from typing import Annotated

import openpyxl
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select

from app.api.deps import DbSession, require_permission
from app.models.enums import AuditAction, WorkloadCategory
from app.models.user import User
from app.models.workload_norm import AdditionalWorkloadNorm
from app.schemas.workload_norm import WorkloadNormOut, WorkloadNormUpdate
from app.services.audit import log_action
from app.services.crud_base import AuditedRepository

router = APIRouter(prefix="/workload-norms", tags=["workload-norms"])

repo = AuditedRepository(AdditionalWorkloadNorm)

ViewUser = Annotated[User, Depends(require_permission("WORKLOAD_NORMS", "VIEW"))]
WriteUser = Annotated[User, Depends(require_permission("WORKLOAD_NORMS", "UPDATE"))]
ExportUser = Annotated[User, Depends(require_permission("WORKLOAD_NORMS", "EXPORT"))]

WORKLOAD_CATEGORY_LABELS = {
    WorkloadCategory.GENERAL_CONSTRUCTION_ENGINEER: "Инженер ТН по общестроительным работам",
    WorkloadCategory.UTILITY_NETWORKS_ENGINEER: "Инженер ТН по инженерным сетям",
    WorkloadCategory.GROUP_DIVISION_HEAD_ON_SITE_CENTER: "РГ, РУ на объектах (филиалы Ц-З, Ц-С)",
    WorkloadCategory.GROUP_HEAD_K2_CENTER: "РГ K2 BI / K2+ фасады либо геодезия (филиалы Ц-З, Ц-С)",
    WorkloadCategory.GROUP_DIVISION_HEAD_EXTERNAL_CENTER: "РГ, РУ на внешних проектах, доля ≥50% (филиалы Ц-З, Ц-С)",
    WorkloadCategory.BRANCH_DIRECTOR_K2_CENTER: "ДФ (К2) (филиалы Ц-З, Ц-С)",
    WorkloadCategory.BRANCH_DIRECTOR_K2_EXTERNAL_CENTER: "ДФ (К2+Внешние) (филиалы Ц-З, Ц-С)",
    WorkloadCategory.GROUP_HEAD_ALMATY_SHYMKENT: "РГ (филиал Алматы, Шымкент)",
    WorkloadCategory.DIVISION_HEAD_ALMATY_SHYMKENT: "РУ (филиал Алматы, Шымкент)",
    WorkloadCategory.BRANCH_DIRECTOR_ALMATY_SHYMKENT: "ДФ (филиал Алматы, Шымкент)",
}


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


@router.get("/export")
def export_workload_norms(db: DbSession, user: ExportUser):
    """Экспорт норм дополнительной нагрузки в Excel — формирование запроса
    для выгрузки данных вне системы (регламент BIG-HRM-RGL-038-RU)."""
    rows = db.scalars(select(AdditionalWorkloadNorm).order_by(AdditionalWorkloadNorm.Category)).all()

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Доп. нагрузки ТН"
    sheet.append([
        "Категория", "Норма, м²", "Сигнал к привлечению помощника, м²",
        "Предел, выше которого расчёт не производится, м²", "Коэффициент", "Ссылка на расчёт метрики",
    ])
    for r in rows:
        sheet.append([
            WORKLOAD_CATEGORY_LABELS.get(r.Category, r.Category.value),
            r.NormValue,
            r.SignalValue,
            r.LimitValue,
            float(r.Coefficient) if r.Coefficient is not None else None,
            r.MetricLinkUrl or "",
        ])

    log_action(
        db, table_name="AdditionalWorkloadNorms", record_id=uuid.uuid4(), action=AuditAction.EXPORT,
        user_id=user.Id, reason="Экспорт норм дополнительной нагрузки",
    )
    db.commit()

    buffer = BytesIO()
    workbook.save(buffer)
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=workload_norms_export.xlsx"},
    )
