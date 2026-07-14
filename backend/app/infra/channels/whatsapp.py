from typing import Any

from app.core.exceptions import DomainValidationError
from app.domain.entities.inbound_message import InboundMessage
from app.domain.enums import Channel


def normalize(payload: dict[str, Any]) -> InboundMessage:
    """Normalize a WhatsApp payload.

    Supports a simplified WhatsApp Cloud API shape:
    {"entry": [{"changes": [{"value": {
        "contacts": [{"profile": {"name": "..."}, "wa_id": "5571999999999"}],
        "messages": [{"id": "wamid...", "from": "5571999999999", "text": {"body": "..."}}]
    }}]}]}

    And a flat demo shape:
    {"from": "+5571999999999", "name": "...", "message": "...", "id": "...",
     "tenant_slug": "..."}
    """
    if "entry" in payload:
        try:
            value = payload["entry"][0]["changes"][0]["value"]
            msg = value["messages"][0]
            contact = (value.get("contacts") or [{}])[0]
            phone = msg.get("from") or contact.get("wa_id")
            return InboundMessage(
                channel=Channel.WHATSAPP,
                external_id=msg.get("id"),
                external_conversation_id=phone,
                tenant_slug=payload.get("tenant_slug"),
                sender_name=(contact.get("profile") or {}).get("name") or "WhatsApp user",
                sender_phone=_normalize_phone(phone),
                message=(msg.get("text") or {}).get("body") or "",
                metadata={"source": "whatsapp_cloud_api"},
            )
        except (KeyError, IndexError) as exc:
            raise DomainValidationError("Malformed WhatsApp Cloud API payload") from exc

    message = payload.get("message") or payload.get("text")
    phone = payload.get("from") or payload.get("phone")
    if not message or not phone:
        raise DomainValidationError("WhatsApp payload must include 'from' and 'message'")
    return InboundMessage(
        channel=Channel.WHATSAPP,
        external_id=payload.get("id") or payload.get("external_id"),
        external_conversation_id=str(phone),
        tenant_slug=payload.get("tenant_slug"),
        sender_name=payload.get("name") or "WhatsApp user",
        sender_phone=_normalize_phone(str(phone)),
        message=message,
        metadata={"source": "whatsapp_demo"},
    )


def _normalize_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    phone = phone.strip()
    return phone if phone.startswith("+") else f"+{phone}"
