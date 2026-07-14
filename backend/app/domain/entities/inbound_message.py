from typing import Any

from pydantic import BaseModel

from app.domain.enums import Channel


class InboundMessage(BaseModel):
    """Normalized message coming from any external channel adapter."""

    channel: Channel
    external_id: str | None = None
    external_conversation_id: str | None = None
    tenant_slug: str | None = None
    sender_name: str = "Unknown"
    sender_phone: str | None = None
    sender_email: str | None = None
    message: str
    title: str | None = None
    metadata: dict[str, Any] = {}
