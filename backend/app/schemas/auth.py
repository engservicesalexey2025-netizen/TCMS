import uuid

from pydantic import BaseModel

from app.models.enums import RoleCode


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    Id: uuid.UUID
    Login: str
    Email: str
    RoleCode: RoleCode
    EmployeeId: uuid.UUID | None = None

    model_config = {"from_attributes": True}
