from typing import Any

from app.infra.database.repositories.base import BaseRepository, serialize


class ChannelPayloadRepository(BaseRepository):
    collection_name = "channel_payloads"

    async def get_by_external_id(
        self, channel: str, external_id: str
    ) -> dict[str, Any] | None:
        return serialize(
            await self.col.find_one({"channel": channel, "external_id": external_id})
        )
