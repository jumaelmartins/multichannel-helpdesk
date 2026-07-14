import logging
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.application.services.ticket_service import TicketService
from app.core.exceptions import DomainValidationError
from app.core.logging import log_event
from app.domain.entities.inbound_message import InboundMessage
from app.domain.enums import SenderType
from app.infra.database.repositories.channel_payload_repository import ChannelPayloadRepository
from app.infra.database.repositories.contact_repository import ContactRepository
from app.infra.database.repositories.tenant_repository import TenantRepository

logger = logging.getLogger("helpdesk.webhooks")


class WebhookService:
    def __init__(self, db: AsyncDatabase):
        self.payloads = ChannelPayloadRepository(db)
        self.tenants = TenantRepository(db)
        self.contacts = ContactRepository(db)
        self.ticket_service = TicketService(db)

    async def process_inbound(
        self, inbound: InboundMessage, raw_payload: dict[str, Any]
    ) -> dict[str, Any]:
        if inbound.external_id:
            existing = await self.payloads.get_by_external_id(
                inbound.channel, inbound.external_id
            )
            if existing:
                log_event(
                    logger, "webhook_duplicate", channel=inbound.channel,
                    external_id=inbound.external_id,
                )
                return {"duplicate": True, "ticket_id": existing.get("ticket_id")}

        tenant = await self._resolve_tenant(inbound)
        if not tenant:
            await self.payloads.insert(
                {
                    "channel": inbound.channel,
                    "external_id": inbound.external_id,
                    "ticket_id": None,
                    "raw_payload": raw_payload,
                    "processed": False,
                }
            )
            log_event(logger, "webhook_tenant_not_identified", channel=inbound.channel)
            raise DomainValidationError(
                "Unable to identify tenant from payload (unknown slug/phone/email)"
            )

        await self._ensure_contact(tenant["id"], inbound)

        open_ticket = await self.ticket_service.tickets.find_open_by_contact(
            tenant["id"], phone=inbound.sender_phone, email=inbound.sender_email
        )

        if open_ticket:
            message = await self.ticket_service.add_message(
                open_ticket["id"],
                sender_type=SenderType.TENANT,
                sender_name=inbound.sender_name,
                sender_contact=inbound.sender_phone or inbound.sender_email,
                channel=inbound.channel,
                message=inbound.message,
                metadata=inbound.metadata,
            )
            ticket, created = await self.ticket_service.get_ticket(open_ticket["id"]), False
            message_id = message["id"]
        else:
            title = inbound.title or inbound.message[:80]
            ticket = await self.ticket_service.create_ticket(
                {
                    "tenant_id": tenant["id"],
                    "requester": {
                        "name": inbound.sender_name,
                        "email": inbound.sender_email,
                        "phone": inbound.sender_phone,
                        "channel": inbound.channel,
                    },
                    "title": title,
                    "description": inbound.message,
                    "type": "support",
                    "priority": "medium",
                    "source_channel": inbound.channel,
                    "metadata": {
                        "origin": "webhook",
                        "external_conversation_id": inbound.external_conversation_id,
                    },
                },
                created_by=f"webhook:{inbound.channel}",
            )
            message = await self.ticket_service.add_message(
                ticket["id"],
                sender_type=SenderType.TENANT,
                sender_name=inbound.sender_name,
                sender_contact=inbound.sender_phone or inbound.sender_email,
                channel=inbound.channel,
                message=inbound.message,
                metadata=inbound.metadata,
                notify=False,
            )
            created, message_id = True, message["id"]

        await self.payloads.insert(
            {
                "channel": inbound.channel,
                "external_id": inbound.external_id,
                "ticket_id": ticket["id"],
                "raw_payload": raw_payload,
                "processed": True,
            }
        )
        log_event(
            logger, "webhook_processed", channel=inbound.channel,
            ticket=ticket["code"], created=created,
        )
        return {
            "duplicate": False,
            "created": created,
            "ticket_id": ticket["id"],
            "ticket_code": ticket["code"],
            "message_id": message_id,
        }

    async def _resolve_tenant(self, inbound: InboundMessage) -> dict[str, Any] | None:
        if inbound.tenant_slug:
            tenant = await self.tenants.get_by_slug(inbound.tenant_slug)
            if tenant:
                return tenant
        contact = None
        if inbound.sender_phone:
            contact = await self.contacts.get_by_phone(inbound.sender_phone)
        if not contact and inbound.sender_email:
            contact = await self.contacts.get_by_email(inbound.sender_email)
        if contact:
            return await self.tenants.get(contact["tenant_id"])
        return None

    async def _ensure_contact(self, tenant_id: str, inbound: InboundMessage) -> None:
        if not inbound.sender_phone and not inbound.sender_email:
            return
        contact = None
        if inbound.sender_phone:
            contact = await self.contacts.get_by_phone(inbound.sender_phone)
        if not contact and inbound.sender_email:
            contact = await self.contacts.get_by_email(inbound.sender_email)
        if not contact:
            await self.contacts.insert(
                {
                    "tenant_id": tenant_id,
                    "name": inbound.sender_name,
                    "email": inbound.sender_email,
                    "phone": inbound.sender_phone,
                    "role": None,
                    "channels": [inbound.channel],
                }
            )
