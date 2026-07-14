import os

os.environ["MONGODB_DATABASE"] = "helpdesk_test"
os.environ["JWT_SECRET"] = "test-secret-key-with-at-least-32-bytes!"
os.environ["DEMO_MODE"] = "true"
os.environ["WEBHOOK_TOKEN"] = "test-webhook-token"

import pytest  # noqa: E402
from asgi_lifespan import LifespanManager  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.infra.database.mongodb import get_db  # noqa: E402
from app.main import create_app  # noqa: E402

WEBHOOK_HEADERS = {"X-Webhook-Token": "test-webhook-token"}


@pytest.fixture(scope="session")
async def client():
    app = create_app()
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as http:
            yield http


@pytest.fixture(scope="session")
async def seeded(client):
    """Reset DB and create baseline users/tenants once per test session."""
    db = get_db()
    for name in ["tickets", "ticket_messages", "ticket_events", "channel_payloads",
                 "notifications", "contacts", "tenants", "users", "counters"]:
        await db[name].delete_many({})

    from datetime import UTC, datetime

    now = datetime.now(UTC)
    tenants = {}
    for name, slug in [("Demo Telecom", "demo-telecom"), ("Fiber Works", "fiber-works")]:
        result = await db.tenants.insert_one(
            {"name": name, "slug": slug, "document": None, "status": "active",
             "created_at": now, "updated_at": now}
        )
        tenants[slug] = str(result.inserted_id)

    password = hash_password("demo123")
    users = {}
    for name, email, role, tenant_id in [
        ("Admin Demo", "admin@demo.com", "admin", None),
        ("Agente Demo", "agent@demo.com", "agent", None),
        ("Cliente Demo", "tenant@demo.com", "tenant_user", tenants["demo-telecom"]),
        ("Viewer Demo", "viewer@demo.com", "viewer", None),
    ]:
        result = await db.users.insert_one(
            {"name": name, "email": email, "password_hash": password, "role": role,
             "tenant_id": tenant_id, "created_at": now, "updated_at": now}
        )
        users[email] = str(result.inserted_id)

    # A known contact so webhooks can resolve tenant by phone
    await db.contacts.insert_one(
        {"tenant_id": tenants["demo-telecom"], "name": "Carlos Silva",
         "email": "carlos@demo.com", "phone": "+5571999999999", "role": None,
         "channels": ["whatsapp"], "created_at": now, "updated_at": now}
    )
    return {"tenants": tenants, "users": users}


async def login(client: AsyncClient, email: str, password: str = "demo123") -> dict:
    response = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
async def admin_headers(client, seeded):
    return await login(client, "admin@demo.com")


@pytest.fixture(scope="session")
async def agent_headers(client, seeded):
    return await login(client, "agent@demo.com")


@pytest.fixture(scope="session")
async def tenant_headers(client, seeded):
    return await login(client, "tenant@demo.com")


@pytest.fixture(scope="session")
async def viewer_headers(client, seeded):
    return await login(client, "viewer@demo.com")


@pytest.fixture
async def make_ticket(client, admin_headers, seeded):
    async def _make(**overrides):
        payload = {
            "tenant_id": seeded["tenants"]["demo-telecom"],
            "requester": {"name": "Carlos Silva", "email": "carlos@demo.com",
                          "phone": "+5571999999999", "channel": "manual"},
            "title": "Test ticket title",
            "description": "Test description",
            "type": "bug",
            "priority": "high",
            "source_channel": "manual",
            **overrides,
        }
        response = await client.post("/api/tickets", json=payload, headers=admin_headers)
        assert response.status_code == 201, response.text
        return response.json()

    return _make
