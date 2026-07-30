"""Личный кабинет (§7 ТЗ) — сводная витрина о текущем пользователе. Отдельно
от лёгкого `/auth/me` (используется фронтендом на каждый запрос для
гардов) — здесь можно позволить себе более тяжёлые join'ы."""
from sqlalchemy import select

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.models.assignment import Assignment
from app.models.employee import Employee
from app.models.org import OrgUnit, Position
from app.models.project import Project
from app.models.user import Role
from app.schemas.profile import ActiveProjectOut, ProfileOut
from app.services.permissions import get_active_role_ids

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me", response_model=ProfileOut)
def read_profile(db: DbSession, user: CurrentUser) -> ProfileOut:
    role_ids = get_active_role_ids(db, user)
    role_names = (
        list(db.scalars(select(Role.Name).where(Role.Id.in_(role_ids))).all())
        if role_ids
        else []
    )

    employee = db.get(Employee, user.EmployeeId) if user.EmployeeId else None
    position_name = None
    org_unit_name = None
    corporate_phone = None
    active_projects: list[ActiveProjectOut] = []

    if employee is not None:
        corporate_phone = employee.CorporatePhone
        if employee.PositionId:
            position_name = db.scalar(select(Position.Name).where(Position.Id == employee.PositionId))
        if employee.OrgUnitId:
            org_unit_name = db.scalar(select(OrgUnit.Name).where(OrgUnit.Id == employee.OrgUnitId))
        rows = db.execute(
            select(Project.Id, Project.Name)
            .join(Assignment, Assignment.ProjectId == Project.Id)
            .where(Assignment.EmployeeId == employee.Id, Assignment.PeriodEnd.is_(None))
        ).all()
        active_projects = [ActiveProjectOut(Id=pid, Name=name) for pid, name in rows]

    return ProfileOut(
        Id=user.Id,
        Login=user.Login,
        Email=user.Email,
        FullName=employee.FullName if employee else None,
        Position=position_name,
        OrgUnit=org_unit_name,
        CorporatePhone=corporate_phone,
        LastLoginAt=user.LastLoginAt,
        Roles=role_names,
        ActiveProjects=active_projects,
    )
