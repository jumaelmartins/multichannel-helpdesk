from typing import Any

from app.infra.database.repositories.base import BaseRepository, serialize


class ContactRepository(BaseRepository):
    collection_name = "contacts"

    async def get_by_phone(self, phone: str) -> dict[str, Any] | None:
        return serialize(await self.col.find_one({"phone": phone}))

    async def get_by_email(self, email: str) -> dict[str, Any] | None:
        return serialize(await self.col.find_one({"email": email.lower()}))
