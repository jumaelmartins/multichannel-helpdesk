from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.domain.enums import EventType


class TicketEvent(BaseModel):
    id: str
    ticket_id: str
    event_type: EventType
    old_value: str | None = None
    new_value: str | None = None
    description: str = ""
    created_by: str = "system"
    created_at: datetime
    metadata: dict[str, Any] = {}
