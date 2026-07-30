import uuid

from pydantic import BaseModel, ConfigDict


class RoleLookupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: uuid.UUID
    # str, не RoleCode: роли теперь создаются администратором через
    # Конструктор (§16 ТЗ) с произвольным кодом, не ограниченным исходным
    # перечислением из 5 значений.
    Code: str
    Name: str


class ProjectLookupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: uuid.UUID
    Name: str
