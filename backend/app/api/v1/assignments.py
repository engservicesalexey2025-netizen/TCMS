import uuid
from io import BytesIO
from typing import Annotated

import openpyxl
from fastapi import APIRouter, Depends, Response
from sqlalchemy import select

from app.api.deps import DbSession, require_permission
from app.api.v1.crud_router import build_crud_router
from app.models.assignment import Assignment, AssignmentRole
from app.models.employee import Employee
from app.models.enums import AuditAction
from app.models.project import Project
from app.models.user import User
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentOut,
    AssignmentRoleCreate,
    AssignmentRoleOut,
    AssignmentUpdate,
)
from app.services.audit import log_action
from app.services.crud_base import AuditedRepository

router = build_crud_router(
    model=Assignment,
    create_schema=AssignmentCreate,
    update_schema=AssignmentUpdate,
    out_schema=AssignmentOut,
    prefix="/assignments",
    tags=["assignments"],
    module="ASSIGNMENTS",
    scoped=True,
)

assignment_roles_router = build_crud_router(
    model=AssignmentRole,
    create_schema=AssignmentRoleCreate,
    update_schema=AssignmentRoleCreate,
    out_schema=AssignmentRoleOut,
    prefix="/assignment-roles",
    tags=["assignment-roles"],
    search_fields=["Name"],
    module="ASSIGNMENT_ROLES",
)

# Отдельный роутер под тем же префиксом — регистрируется в router.py ДО
# основного (generic) router'а выше, иначе GET /assignments/export
# перехватывается GET /assignments/{item_id} (см. тот же баг с
# /org-units/export-specialists ранее в этой сессии).
assignments_extra_router = APIRouter(prefix="/assignments", tags=["assignments"])

ExportAssignments = Annotated[User, Depends(require_permission("ASSIGNMENTS", "EXPORT"))]

_assignment_repo = AuditedRepository(Assignment)


@assignments_extra_router.get("/export")
def export_assignments(
    db: DbSession,
    user: ExportAssignments,
    search: str | None = None,
    include_archived: bool = False,
):
    """Экспорт назначений в Excel — тот же формат столбцов, что принимает
    /imports/assignments для массовой загрузки обратно (см. import_profiles.py)."""
    items, _total = _assignment_repo.list(
        db, skip=0, limit=1_000_000, search=search, include_archived=include_archived, user=user,
    )

    employees = {e.Id: e.FullName for e in db.scalars(select(Employee)).all()}
    projects = {p.Id: p.Name for p in db.scalars(select(Project)).all()}
    roles = {r.Id: r.Name for r in db.scalars(select(AssignmentRole)).all()}

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Назначения"
    sheet.append([
        "Сотрудник", "Проект", "Роль на проекте", "Загрузка",
        "Начало на проекте", "Окончание на проекте", "Комментарий",
    ])
    for a in items:
        sheet.append([
            employees.get(a.EmployeeId, ""),
            projects.get(a.ProjectId, ""),
            roles.get(a.RoleOnProjectId, "") if a.RoleOnProjectId else "",
            float(a.Workload) if a.Workload is not None else None,
            a.PeriodStart.strftime("%d.%m.%Y") if a.PeriodStart else "",
            a.PeriodEnd.strftime("%d.%m.%Y") if a.PeriodEnd else "",
            a.Comment or "",
        ])

    log_action(
        db, table_name="Assignments", record_id=uuid.uuid4(), action=AuditAction.EXPORT,
        user_id=user.Id, reason=f"Экспорт списка назначений (search={search!r})",
    )
    db.commit()

    buffer = BytesIO()
    workbook.save(buffer)
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=assignments_export.xlsx"},
    )
