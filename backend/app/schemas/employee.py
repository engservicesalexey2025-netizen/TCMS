import re
import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, field_validator

from app.models.enums import AuditAction, EmployeeStatus
from app.models.enums import Gender as GenderEnum
from app.schemas.common import AuditFields


class TenureOut(BaseModel):
    Years: int
    Months: int
    TotalDays: int


def _blank_to_none(value: str | None) -> str | None:
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


class EmployeeCreate(BaseModel):
    FullName: str
    IIN: str
    Email: EmailStr
    CorporatePhone: str | None = None
    PersonalPhone: str | None = None
    CityId: uuid.UUID
    BirthDate: date
    Gender: GenderEnum
    LegalEntityId: uuid.UUID
    PositionId: uuid.UUID | None = None
    OrgUnitId: uuid.UUID | None = None
    HireDate: date | None = None
    Status: EmployeeStatus = EmployeeStatus.ACTIVE
    Salary: float | None = None
    Comment: str | None = None

    @field_validator("IIN")
    @classmethod
    def _validate_iin(cls, value: str) -> str:
        if not re.fullmatch(r"\d{12}", value):
            raise ValueError("ИИН должен состоять из 12 цифр")
        return value


class EmployeeUpdate(BaseModel):
    FullName: str | None = None
    IIN: str | None = None
    Email: str | None = None
    CorporatePhone: str | None = None
    PersonalPhone: str | None = None
    CityId: uuid.UUID | None = None
    BirthDate: date | None = None
    Gender: GenderEnum | None = None
    LegalEntityId: uuid.UUID | None = None
    PositionId: uuid.UUID | None = None
    OrgUnitId: uuid.UUID | None = None
    HireDate: date | None = None
    DismissalDate: date | None = None
    Status: EmployeeStatus | None = None
    Salary: float | None = None
    Comment: str | None = None

    @field_validator("IIN", mode="before")
    @classmethod
    def _iin_blank_to_none(cls, value):
        return _blank_to_none(value)

    @field_validator("Email", mode="before")
    @classmethod
    def _email_blank_to_none(cls, value):
        return _blank_to_none(value)

    @field_validator("IIN")
    @classmethod
    def _validate_iin(cls, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(r"\d{12}", value):
            raise ValueError("ИИН должен состоять из 12 цифр")
        return value


class EmployeeOut(AuditFields):
    FullName: str
    # IIN/PersonalPhone default to None (не "обязательные, но nullable") — так
    # ключ можно вообще не передавать при HIDDEN-режиме field_security, и он
    # не попадёт в ответ API благодаря response_model_exclude_unset (§14 ТЗ:
    # "не передаётся через API", а не просто null).
    IIN: str | None = None
    Email: str | None
    CorporatePhone: str | None
    PersonalPhone: str | None = None
    CityId: uuid.UUID | None
    BirthDate: date | None
    Gender: GenderEnum | None
    LegalEntityId: uuid.UUID | None
    PositionId: uuid.UUID | None
    OrgUnitId: uuid.UUID | None
    HireDate: date | None
    DismissalDate: date | None
    Status: EmployeeStatus
    Salary: float | None
    CorporateTenure: TenureOut | None = None


class EmployeeHistoryEntryOut(BaseModel):
    Id: uuid.UUID
    Action: AuditAction
    ChangedByUserId: uuid.UUID | None
    ChangedByLogin: str | None
    ChangedDate: datetime
    FieldName: str | None
    OldValue: str | None
    NewValue: str | None
