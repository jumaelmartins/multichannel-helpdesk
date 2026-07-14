import logging
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.core.logging import log_event
from app.infra.database.repositories.notification_repository import NotificationRepository

logger = logging.getLogger("helpdesk.notifications")


class NotificationService:
    def __init__(self, db: AsyncDatabase):
        self.repo = NotificationRepository(db)

    async def notify_internal(self, title: str, body: str, ticket: dict[str, Any] | None = None):
        doc = {
            "audience": "internal",
            "tenant_id": ticket.get("tenant_id") if ticket else None,
            "ticket_id": ticket.get("id") if ticket else None,
            "ticket_code": ticket.get("code") if ticket else None,
            "title": title,
            "body": body,
            "read": False,
        }
        await self.repo.insert(doc)
        log_event(logger, "internal_notification", title=title, ticket=doc["ticket_code"])

    async def notify_tenant(self, title: str, body: str, ticket: dict[str, Any]):
        doc = {
            "audience": "tenant",
            "tenant_id": ticket.get("tenant_id"),
            "ticket_id": ticket.get("id"),
            "ticket_code": ticket.get("code"),
            "title": title,
            "body": body,
            "read": False,
        }
        await self.repo.insert(doc)
        # Fake email/channel delivery for the public demo: structured log only.
        log_event(
            logger,
            "tenant_notification",
            title=title,
            ticket=doc["ticket_code"],
            channel=ticket.get("source_channel"),
            to=(ticket.get("requester") or {}).get("email"),
        )

    async def list_for(self, role: str, tenant_id: str | None) -> list[dict[str, Any]]:
        return await self.repo.list_for(role, tenant_id)

    async def unread_count(self, role: str, tenant_id: str | None) -> int:
        return await self.repo.unread_count(role, tenant_id)

    async def mark_read(self, notification_id: str) -> None:
        await self.repo.mark_read(notification_id)

    async def mark_all_read(self, role: str, tenant_id: str | None) -> None:
        await self.repo.mark_all_read(role, tenant_id)
