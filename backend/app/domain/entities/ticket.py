from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.enums import Channel, TicketPriority, TicketStatus, TicketType


class Requester(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    channel: Channel = Channel.MANUAL


class SlaInfo(BaseModel):
    first_response_due_at: datetime | None = None
    resolution_due_at: datetime | None = None
    first_response_at: datetime | None = None


class Attachment(BaseModel):
    type: str = "file"
    url: str
    filename: str


class Ticket(BaseModel):
    id: str
    code: str
    tenant_id: str
    requester: Requester
    title: str
    description: str
    type: TicketType
    priority: TicketPriority
    status: TicketStatus = TicketStatus.OPEN
    source_channel: Channel = Channel.MANUAL
    assigned_to: str | None = None
    sla: SlaInfo = Field(default_factory=SlaInfo)
    tags: list[str] = []
    metadata: dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None
    closed_at: datetime | None = None
