from typing import Any

from pymongo import ReturnDocument

from app.infra.database.repositories.base import BaseRepository, serialize


class TicketRepository(BaseRepository):
    collection_name = "tickets"

    async def next_code_sequence(self) -> int:
        counter = await self.col.database.counters.find_one_and_update(
            {"_id": "ticket_code"},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return counter["seq"]

    async def get_by_code(self, code: str) -> dict[str, Any] | None:
        return serialize(await self.col.find_one({"code": code.upper()}))

    async def find_open_by_contact(
        self, tenant_id: str, phone: str | None = None, email: str | None = None
    ) -> dict[str, Any] | None:
        active = ["open", "in_analysis", "in_progress", "waiting_customer", "waiting_internal"]
        contact_filters: list[dict[str, Any]] = []
        if phone:
            contact_filters.append({"requester.phone": phone})
        if email:
            contact_filters.append({"requester.email": email})
        if not contact_filters:
            return None
        doc = await self.col.find_one(
            {"tenant_id": tenant_id, "status": {"$in": active}, "$or": contact_filters},
            sort=[("created_at", -1)],
        )
        return serialize(doc)

    @staticmethod
    def build_filters(
        tenant_id: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        ticket_type: str | None = None,
        channel: str | None = None,
        assigned_to: str | None = None,
        search: str | None = None,
        statuses: list[str] | None = None,
    ) -> dict[str, Any]:
        filters: dict[str, Any] = {}
        if tenant_id:
            filters["tenant_id"] = tenant_id
        if status:
            filters["status"] = status
        elif statuses:
            filters["status"] = {"$in": statuses}
        if priority:
            filters["priority"] = priority
        if ticket_type:
            filters["type"] = ticket_type
        if channel:
            filters["source_channel"] = channel
        if assigned_to:
            filters["assigned_to"] = assigned_to
        if search:
            filters["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
                {"code": {"$regex": search, "$options": "i"}},
            ]
        return filters
