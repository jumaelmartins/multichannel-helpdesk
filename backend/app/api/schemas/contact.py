from pydantic import BaseModel, EmailStr

from app.domain.enums import Channel


class ContactCreateRequest(BaseModel):
    tenant_id: str
    name: str
    email: EmailStr | None = None
    phone: str | None = None
    role: str | None = None
    channels: list[Channel] = []


class ContactUpdateRequest(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    role: str | None = None
    channels: list[Channel] | None = None
