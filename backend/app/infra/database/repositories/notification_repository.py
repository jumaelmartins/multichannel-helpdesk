from typing import Any

from app.infra.database.repositories.base import BaseRepository, to_object_id


class NotificationRepository(BaseRepository):
    collection_name = "notifications"

    def _audience_filter(self, role: str, tenant_id: str | None) -> dict[str, Any]:
        if role == "tenant_user":
            return {"audience": "tenant", "tenant_id": tenant_id}
        return {"audience": "internal"}

    async def list_for(self, role: str, tenant_id: str | None, limit: int = 30) -> list[dict]:
        return await self.find(
            self._audience_filter(role, tenant_id), sort=[("created_at", -1)], limit=limit
        )

    async def unread_count(self, role: str, tenant_id: str | None) -> int:
        return await self.count({**self._audience_filter(role, tenant_id), "read": False})

    async def mark_read(self, notification_id: str) -> None:
        await self.col.update_one({"_id": to_object_id(notification_id)}, {"$set": {"read": True}})

    async def mark_all_read(self, role: str, tenant_id: str | None) -> None:
        await self.col.update_many(self._audience_filter(role, tenant_id), {"$set": {"read": True}})
