from typing import Any

from pydantic import BaseModel, Field

from app.domain.enums import Channel, TicketPriority, TicketStatus, TicketType


class RequesterPayload(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    channel: Channel = Channel.MANUAL


class AttachmentPayload(BaseModel):
    type: str = "file"
    url: str
    filename: str


class TicketCreateRequest(BaseModel):
    tenant_id: str | None = None  # ignored for tenant users (forced to their tenant)
    requester: RequesterPayload | None = None
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=10_000)
    type: TicketType = TicketType.SUPPORT
    priority: TicketPriority = TicketPriority.MEDIUM
    source_channel: Channel = Channel.MANUAL
    tags: list[str] = []
    metadata: dict[str, Any] = {}


class TicketUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=10_000)
    type: TicketType | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None


class TicketMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10_000)
    attachments: list[AttachmentPayload] = Field(default=[], max_length=10)


class StatusChangeRequest(BaseModel):
    status: TicketStatus


class PriorityChangeRequest(BaseModel):
    priority: TicketPriority


class AssignRequest(BaseModel):
    user_id: str | None = None  # null unassigns


class ResolveRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10_000)
