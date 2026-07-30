"""Чистые функции маскирования/вычислений, переиспользуемые
`app.services.field_security` (движок Column-Level Security, §14 ТЗ) —
сама точка принятия решения "кому что видно" здесь больше не живёт, она в
ColumnPermissions/field_security.py.
"""
from datetime import date

from app.schemas.employee import TenureOut


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
