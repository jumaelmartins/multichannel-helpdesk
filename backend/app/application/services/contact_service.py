from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.core.exceptions import NotFoundError
from app.infra.database.repositories.contact_repository import ContactRepository


class ContactService:
    def __init__(self, db: AsyncDatabase):
        self.contacts = ContactRepository(db)

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        return await self.contacts.insert(data)

    async def list(self, tenant_id: str | None = None) -> list[dict[str, Any]]:
        filters = {"tenant_id": tenant_id} if tenant_id else {}
        return await self.contacts.find(filters, sort=[("name", 1)], limit=500)

    async def get(self, contact_id: str) -> dict[str, Any]:
        contact = await self.contacts.get(contact_id)
        if not contact:
            raise NotFoundError("Contact not found")
        return contact

    async def update(self, contact_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        await self.get(contact_id)
        return await self.contacts.update(contact_id, updates)
