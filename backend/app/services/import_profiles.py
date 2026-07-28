"""Declarative per-entity Excel import configuration.

Adding import support for another entity is one new IMPORT_PROFILES entry —
no new endpoint or pipeline code (Тома 1А §20 "Конструктор, а не программист"),
mirroring how app/api/v1/crud_router.py's build_crud_router configures a new
CRUD resource.
"""
from dataclasses import dataclass, field
from typing import Any, Literal, Type

from pydantic import BaseModel

from app.models.employee import Employee
from app.models.enums import EmployeeStatus, Gender, RoleCode
from app.models.org import City, LegalEntity, OrgUnit, Position
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.schemas.org import PositionCreate
from app.services.crud_base import AuditedRepository

ColumnKind = Literal["text", "date", "enum", "fk_lookup"]


@dataclass
class ColumnSpec:
    field: str
    header_aliases: list[str]
    required: bool = False
    kind: ColumnKind = "text"
    enum_cls: Type | None = None
    enum_map: dict[str, str] | None = None
    fk_model: Type | None = None
    fk_lookup_field: str = "Name"


@dataclass
class ImportProfile:
    entity_type: str
    model: Type
    repo: AuditedRepository
    match_fields: list[str]
    columns: list[ColumnSpec]
    create_schema: Type[BaseModel]
    update_schema: Type[BaseModel]
    write_roles: tuple[RoleCode, ...] = field(default_factory=tuple)


IMPORT_PROFILES: dict[str, ImportProfile] = {
    "positions": ImportProfile(
        entity_type="positions",
        model=Position,
        repo=AuditedRepository(Position, search_fields=["Name"]),
        match_fields=["Name"],
        columns=[
            ColumnSpec("Name", ["Наименование", "Должность"], required=True),
        ],
        create_schema=PositionCreate,
        update_schema=PositionCreate,
        write_roles=(RoleCode.ADMIN,),
    ),
    "employees": ImportProfile(
        entity_type="employees",
        model=Employee,
        repo=AuditedRepository(Employee, search_fields=["FullName"]),
        match_fields=["FullName"],
        columns=[
            ColumnSpec("FullName", ["ФИО", "Фамилия Имя Отчество"], required=True),
            ColumnSpec("IIN", ["ИИН"], required=True),
            ColumnSpec("Email", ["Email", "Электронная почта"], required=True),
            ColumnSpec("CorporatePhone", ["Корпоративный телефон"]),
            ColumnSpec("PersonalPhone", ["Личный телефон"]),
            ColumnSpec("CityId", ["Город"], kind="fk_lookup", fk_model=City),
            ColumnSpec("BirthDate", ["Дата рождения"], required=True, kind="date"),
            ColumnSpec(
                "Gender", ["Пол"], required=True, kind="enum", enum_cls=Gender,
                enum_map={"Мужской": "MALE", "Женский": "FEMALE"},
            ),
            ColumnSpec(
                "LegalEntityId", ["Юридическое лицо", "ТОО"],
                kind="fk_lookup", fk_model=LegalEntity,
            ),
            ColumnSpec(
                "PositionId", ["Должность"], kind="fk_lookup", fk_model=Position
            ),
            ColumnSpec(
                "OrgUnitId", ["Подразделение", "Оргединица", "Управление"],
                kind="fk_lookup", fk_model=OrgUnit,
            ),
            ColumnSpec("HireDate", ["Дата приёма", "Дата приема"], kind="date"),
            ColumnSpec(
                "Status", ["Статус"], kind="enum", enum_cls=EmployeeStatus,
                enum_map={
                    "Активен": "ACTIVE",
                    "В отпуске": "ON_LEAVE",
                    "Уволен": "DISMISSED",
                },
            ),
        ],
        create_schema=EmployeeCreate,
        update_schema=EmployeeUpdate,
        write_roles=(RoleCode.ADMIN, RoleCode.DEPARTMENT_HEAD, RoleCode.GROUP_HEAD),
    ),
}


def get_profile(entity_type: str) -> ImportProfile | None:
    return IMPORT_PROFILES.get(entity_type)
