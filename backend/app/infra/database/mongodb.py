from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import get_settings

_client: AsyncMongoClient | None = None


def get_client() -> AsyncMongoClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncMongoClient(settings.mongodb_uri, tz_aware=True)
    return _client


def get_db() -> AsyncDatabase:
    settings = get_settings()
    return get_client()[settings.mongodb_database]


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None


async def ensure_indexes(db: AsyncDatabase) -> None:
    await db.tickets.create_index("code", unique=True)
    await db.tickets.create_index("tenant_id")
    await db.tickets.create_index("status")
    await db.tickets.create_index("priority")
    await db.tickets.create_index("type")
    await db.tickets.create_index("source_channel")
    await db.tickets.create_index("created_at")
    await db.tickets.create_index("updated_at")
    await db.tickets.create_index("assigned_to")
    await db.tickets.create_index([("tenant_id", 1), ("status", 1)])
    await db.tickets.create_index([("tenant_id", 1), ("created_at", -1)])
    await db.tickets.create_index([("status", 1), ("priority", 1)])

    await db.ticket_messages.create_index("ticket_id")
    await db.ticket_messages.create_index("created_at")
    await db.ticket_messages.create_index([("ticket_id", 1), ("created_at", 1)])

    await db.ticket_events.create_index("ticket_id")
    await db.ticket_events.create_index("event_type")
    await db.ticket_events.create_index("created_at")
    await db.ticket_events.create_index([("ticket_id", 1), ("created_at", 1)])

    await db.channel_payloads.create_index("channel")
    await db.channel_payloads.create_index("external_id")
    await db.channel_payloads.create_index("processed")
    await db.channel_payloads.create_index("created_at")

    await db.tenants.create_index("slug", unique=True)
    await db.users.create_index("email", unique=True)
    await db.contacts.create_index("tenant_id")
    await db.contacts.create_index("phone")

    await db.notifications.create_index([("audience", 1), ("read", 1), ("created_at", -1)])
