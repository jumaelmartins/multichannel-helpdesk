from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.domain.entities.ticket import Attachment
from app.domain.enums import Channel, SenderType


class TicketMessage(BaseModel):
    id: str
    ticket_id: str
    sender_type: SenderType
    sender_name: str
    sender_contact: str | None = None
    channel: Channel = Channel.MANUAL
    message: str
    attachments: list[Attachment] = []
    metadata: dict[str, Any] = {}
    created_at: datetime
