from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from app.core.exceptions import NotFoundError


def to_object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError) as exc:
        raise NotFoundError(f"Invalid id: {value}") from exc


def serialize(doc: dict[str, Any] | None) -> dict[str, Any] | None:
    if doc is None:
        return None
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


def utcnow() -> datetime:
    return datetime.now(UTC)


class BaseRepository:
    collection_name: str

    def __init__(self, db: AsyncDatabase):
        self.col = db[self.collection_name]

    async def insert(self, data: dict[str, Any]) -> dict[str, Any]:
        now = utcnow()
        data.setdefault("created_at", now)
        data.setdefault("updated_at", now)
        result = await self.col.insert_one(data)
        return serialize({**data, "_id": result.inserted_id})

    async def get(self, item_id: str) -> dict[str, Any] | None:
        return serialize(await self.col.find_one({"_id": to_object_id(item_id)}))

    async def find(
        self,
        filters: dict[str, Any] | None = None,
        sort: list[tuple[str, int]] | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        cursor = self.col.find(filters or {})
        if sort:
            cursor = cursor.sort(sort)
        cursor = cursor.skip(skip).limit(limit)
        return [serialize(doc) async for doc in cursor]

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        return await self.col.count_documents(filters or {})

    async def update(self, item_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        updates["updated_at"] = utcnow()
        doc = await self.col.find_one_and_update(
            {"_id": to_object_id(item_id)},
            {"$set": updates},
            return_document=ReturnDocument.AFTER,
        )
        return serialize(doc)

    async def delete(self, item_id: str) -> bool:
        result = await self.col.delete_one({"_id": to_object_id(item_id)})
        return result.deleted_count == 1
