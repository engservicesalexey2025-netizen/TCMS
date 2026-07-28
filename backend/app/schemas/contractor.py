from pydantic import BaseModel

from app.schemas.common import AuditFields


class ContractorCreate(BaseModel):
    Name: str
    BinIin: str | None = None
    ContactInfo: str | None = None
    Comment: str | None = None


class ContractorUpdate(BaseModel):
    Name: str | None = None
    BinIin: str | None = None
    ContactInfo: str | None = None
    Comment: str | None = None


class ContractorOut(AuditFields):
    Name: str
    BinIin: str | None
    ContactInfo: str | None
