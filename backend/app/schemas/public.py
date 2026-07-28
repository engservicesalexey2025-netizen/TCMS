import uuid

from pydantic import BaseModel, ConfigDict

from app.models.enums import RoleCode


class RoleLookupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: uuid.UUID
    Code: RoleCode
    Name: str
