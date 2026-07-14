from typing import Any

from app.core.exceptions import DomainValidationError
from app.domain.entities.inbound_message import InboundMessage
from app.domain.enums import Channel


def normalize(payload: dict[str, Any]) -> InboundMessage:
    """Normalize a Telegram Bot API update.

    {"update_id": 123, "tenant_slug": "...",  # tenant_slug is a demo extension
     "message": {"message_id": 1, "from": {"first_name": "...", "username": "..."},
                 "chat": {"id": 42}, "text": "..."}}

    The chat id becomes a synthetic contact identifier ("tg:<chat_id>") so that
    follow-up messages land on the same ticket.
    """
    msg = payload.get("message")
    if not msg or not msg.get("text"):
        raise DomainValidationError("Telegram payload must include message.text")
    sender = msg.get("from") or {}
    chat_id = (msg.get("chat") or {}).get("id")
    name = " ".join(
        part for part in [sender.get("first_name"), sender.get("last_name")] if part
    ) or sender.get("username") or "Telegram user"
    return InboundMessage(
        channel=Channel.TELEGRAM,
        external_id=f"{payload.get('update_id')}" if payload.get("update_id") else None,
        external_conversation_id=str(chat_id) if chat_id else None,
        tenant_slug=payload.get("tenant_slug"),
        sender_name=name,
        sender_phone=f"tg:{chat_id}" if chat_id else None,
        message=msg["text"],
        metadata={"source": "telegram", "username": sender.get("username")},
    )
