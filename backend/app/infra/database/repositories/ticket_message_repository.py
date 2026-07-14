from typing import Any

from app.infra.database.repositories.base import BaseRepository


class TicketMessageRepository(BaseRepository):
    collection_name = "ticket_messages"

    async def list_for_ticket(self, ticket_id: str) -> list[dict[str, Any]]:
        return await self.find({"ticket_id": ticket_id}, sort=[("created_at", 1)], limit=500)
