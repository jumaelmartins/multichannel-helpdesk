from typing import Any

from app.infra.database.repositories.base import BaseRepository, serialize


class TenantRepository(BaseRepository):
    collection_name = "tenants"

    async def get_by_slug(self, slug: str) -> dict[str, Any] | None:
        return serialize(await self.col.find_one({"slug": slug}))
