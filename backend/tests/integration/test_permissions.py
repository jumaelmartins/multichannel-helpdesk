async def test_tenant_user_sees_only_own_tenant(
    client, make_ticket, tenant_headers, seeded
):
    own = await make_ticket()  # demo-telecom (tenant user's tenant)
    other = await make_ticket(tenant_id=seeded["tenants"]["fiber-works"])

    listing = await client.get("/api/tickets?limit=100", headers=tenant_headers)
    tenant_ids = {t["tenant_id"] for t in listing.json()["items"]}
    assert tenant_ids == {seeded["tenants"]["demo-telecom"]}

    ok = await client.get(f"/api/tickets/{own['id']}", headers=tenant_headers)
    assert ok.status_code == 200

    blocked = await client.get(f"/api/tickets/{other['id']}", headers=tenant_headers)
    assert blocked.status_code == 404


async def test_tenant_user_cannot_change_status(client, make_ticket, tenant_headers):
    ticket = await make_ticket()
    response = await client.post(
        f"/api/tickets/{ticket['id']}/status",
        json={"status": "in_analysis"},
        headers=tenant_headers,
    )
    assert response.status_code == 403


async def test_agent_cannot_change_priority_or_assign(
    client, make_ticket, agent_headers, seeded
):
    ticket = await make_ticket()
    priority = await client.post(
        f"/api/tickets/{ticket['id']}/priority",
        json={"priority": "low"},
        headers=agent_headers,
    )
    assert priority.status_code == 403

    assign = await client.post(
        f"/api/tickets/{ticket['id']}/assign",
        json={"user_id": seeded["users"]["agent@demo.com"]},
        headers=agent_headers,
    )
    assert assign.status_code == 403


async def test_viewer_is_read_only(client, viewer_headers, seeded):
    listing = await client.get("/api/tickets", headers=viewer_headers)
    assert listing.status_code == 200

    create = await client.post(
        "/api/tickets",
        json={"tenant_id": seeded["tenants"]["demo-telecom"], "title": "Nope",
              "description": "x", "type": "bug", "priority": "low"},
        headers=viewer_headers,
    )
    assert create.status_code == 403


async def test_only_admin_creates_tenants(client, agent_headers, admin_headers):
    denied = await client.post(
        "/api/tenants", json={"name": "Blocked Tenant"}, headers=agent_headers
    )
    assert denied.status_code == 403

    allowed = await client.post(
        "/api/tenants", json={"name": "Created Tenant"}, headers=admin_headers
    )
    assert allowed.status_code == 201
    assert allowed.json()["slug"] == "created-tenant"


async def test_tenant_user_can_create_and_reply_in_own_tenant(
    client, tenant_headers, seeded
):
    create = await client.post(
        "/api/tickets",
        json={"tenant_id": seeded["tenants"]["fiber-works"],  # must be ignored/forced
              "title": "Tenant opened ticket", "description": "Help",
              "type": "question", "priority": "medium"},
        headers=tenant_headers,
    )
    assert create.status_code == 201
    ticket = create.json()
    assert ticket["tenant_id"] == seeded["tenants"]["demo-telecom"]

    reply = await client.post(
        f"/api/tickets/{ticket['id']}/messages",
        json={"message": "More details here"},
        headers=tenant_headers,
    )
    assert reply.status_code == 201
    assert reply.json()["sender_type"] == "tenant"
