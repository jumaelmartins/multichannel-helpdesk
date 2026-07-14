from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.domain.enums import Channel


class ChannelPayload(BaseModel):
    id: str
    channel: Channel
    external_id: str | None = None
    ticket_id: str | None = None
    raw_payload: dict[str, Any] = {}
    processed: bool = False
    created_at: datetime
