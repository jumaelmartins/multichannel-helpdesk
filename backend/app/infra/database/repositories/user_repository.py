from typing import Any

from app.infra.database.repositories.base import BaseRepository, serialize


class UserRepository(BaseRepository):
    collection_name = "users"

    async def get_by_email(self, email: str) -> dict[str, Any] | None:
        return serialize(await self.col.find_one({"email": email.lower()}))

    async def get_by_name(self, name: str) -> dict[str, Any] | None:
        return serialize(
            await self.col.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})
        )
