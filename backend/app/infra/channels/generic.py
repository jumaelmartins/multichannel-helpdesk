from typing import Any

from app.core.exceptions import DomainValidationError
from app.domain.entities.inbound_message import InboundMessage
from app.domain.enums import Channel


def normalize(payload: dict[str, Any]) -> InboundMessage:
    """Normalize a generic webhook payload.

    Expected shape:
    {
      "tenant_slug": "demo-telecom",       # optional if phone/email identifies a contact
      "external_id": "evt-123",            # optional, used for dedup
      "name": "Carlos Silva",
      "email": "carlos@demo.com",          # optional
      "phone": "+5571999999999",           # optional
      "title": "Short summary",            # optional
      "message": "Full message text"
    }
    """
    message = payload.get("message") or payload.get("text")
    if not message:
        raise DomainValidationError("Payload must include a 'message' field")
    return InboundMessage(
        channel=Channel.WEBHOOK,
        external_id=payload.get("external_id"),
        external_conversation_id=payload.get("conversation_id"),
        tenant_slug=payload.get("tenant_slug"),
        sender_name=payload.get("name") or "Unknown",
        sender_phone=payload.get("phone"),
        sender_email=payload.get("email"),
        message=message,
        title=payload.get("title"),
        metadata={"source": "generic_webhook"},
    )
