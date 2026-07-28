"""Единая точка сериализации Employee: маскирование ИИН/личного телефона по
роли + вычисление стажа. Всё, что отдаёт карточку сотрудника наружу (список,
получение по id, история изменений), обязано проходить через эту точку —
так масштабирование логики не расходится по нескольким копипаст-местам.
"""
from datetime import date

from app.models.employee import Employee
from app.models.enums import RoleCode
from app.models.user import User
from app.schemas.employee import EmployeeOut, TenureOut

FULL_PII_ROLES = {RoleCode.ADMIN, RoleCode.DEPARTMENT_HEAD, RoleCode.GROUP_HEAD}


def mask_iin(iin: str | None) -> str | None:
    if not iin:
        return iin
    return f"********{iin[-4:]}"


def compute_tenure(hire_date: date | None, dismissal_date: date | None) -> TenureOut | None:
    if hire_date is None:
        return None
    end = dismissal_date or date.today()
    total_days = (end - hire_date).days
    years, remainder_days = divmod(total_days, 365)
    months = remainder_days // 30
    return TenureOut(Years=years, Months=months, TotalDays=total_days)


def can_see_full_pii(user: User) -> bool:
    return user.Role.Code in FULL_PII_ROLES


def serialize_employee(emp: Employee, viewer: User) -> EmployeeOut:
    out = EmployeeOut.model_validate(emp, from_attributes=True)
    out.CorporateTenure = compute_tenure(emp.HireDate, emp.DismissalDate)
    if not can_see_full_pii(viewer):
        out.IIN = mask_iin(emp.IIN)
        out.PersonalPhone = None
    return out
