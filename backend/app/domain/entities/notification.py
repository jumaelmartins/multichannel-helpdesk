from datetime import datetime

from pydantic import BaseModel


class Notification(BaseModel):
    id: str
    audience: str = "internal"  # internal | tenant
    user_id: str | None = None
    tenant_id: str | None = None
    ticket_id: str | None = None
    ticket_code: str | None = None
    title: str
    body: str = ""
    read: bool = False
    created_at: datetime
