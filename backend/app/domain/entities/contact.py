from datetime import datetime

from pydantic import BaseModel

from app.domain.enums import Channel


class Contact(BaseModel):
    id: str
    tenant_id: str
    name: str
    email: str | None = None
    phone: str | None = None
    role: str | None = None
    channels: list[Channel] = []
    created_at: datetime
    updated_at: datetime
