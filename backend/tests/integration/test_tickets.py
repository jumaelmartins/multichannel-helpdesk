import re


async def test_create_ticket_generates_code_sla_and_event(client, make_ticket, admin_headers):
    ticket = await make_ticket()
    assert re.fullmatch(r"HD-\d{4,}", ticket["code"])
    assert ticket["status"] == "open"
    assert ticket["sla"]["first_response_due_at"] is not None
    assert ticket["sla_state"] in ("ok", "near_due")

    events = await client.get(f"/api/tickets/{ticket['id']}/events", headers=admin_headers)
    types = [e["event_type"] for e in events.json()]
    assert "ticket_created" in types


async def test_list_tickets_with_status_filter(client, make_ticket, admin_headers):
    await make_ticket(title="Filter target ticket")
    response = await client.get("/api/tickets?status=open", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert all(t["status"] == "open" for t in body["items"])


async def test_get_by_code(client, make_ticket, admin_headers):
    ticket = await make_ticket()
    response = await client.get(f"/api/tickets/code/{ticket['code']}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["id"] == ticket["id"]


async def test_agent_message_sets_first_response(client, make_ticket, agent_headers):
    ticket = await make_ticket()
    response = await client.post(
        f"/api/tickets/{ticket['id']}/messages",
        json={"message": "We are on it"},
        headers=agent_headers,
    )
    assert response.status_code == 201

    detail = await client.get(f"/api/tickets/{ticket['id']}", headers=agent_headers)
    body = detail.json()
    assert body["sla"]["first_response_at"] is not None
    assert body["sla_state"] == "met"


async def test_status_transition_valid_and_invalid(client, make_ticket, admin_headers):
    ticket = await make_ticket()
    ok = await client.post(
        f"/api/tickets/{ticket['id']}/status",
        json={"status": "in_analysis"},
        headers=admin_headers,
    )
    assert ok.status_code == 200
    assert ok.json()["status"] == "in_analysis"

    invalid = await client.post(
        f"/api/tickets/{ticket['id']}/status",
        json={"status": "closed"},  # closed only allowed from resolved
        headers=admin_headers,
    )
    assert invalid.status_code == 422

    direct_resolve = await client.post(
        f"/api/tickets/{ticket['id']}/status",
        json={"status": "resolved"},  # must use /resolve
        headers=admin_headers,
    )
    assert direct_resolve.status_code == 422


async def test_resolve_and_reopen_flow(client, make_ticket, admin_headers):
    ticket = await make_ticket()
    resolved = await client.post(
        f"/api/tickets/{ticket['id']}/resolve",
        json={"message": "Fixed in v2.4"},
        headers=admin_headers,
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"
    assert resolved.json()["resolved_at"] is not None

    reopened = await client.post(
        f"/api/tickets/{ticket['id']}/reopen", headers=admin_headers
    )
    assert reopened.status_code == 200
    assert reopened.json()["status"] == "open"
    assert reopened.json()["resolved_at"] is None

    events = await client.get(f"/api/tickets/{ticket['id']}/events", headers=admin_headers)
    types = [e["event_type"] for e in events.json()]
    assert "ticket_resolved" in types
    assert "ticket_reopened" in types


async def test_priority_change_recalculates_sla(client, make_ticket, admin_headers):
    ticket = await make_ticket(priority="low")
    original_due = ticket["sla"]["first_response_due_at"]
    response = await client.post(
        f"/api/tickets/{ticket['id']}/priority",
        json={"priority": "critical"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["priority"] == "critical"
    assert body["sla"]["first_response_due_at"] < original_due


async def test_assign_ticket(client, make_ticket, admin_headers, seeded):
    ticket = await make_ticket()
    agent_id = seeded["users"]["agent@demo.com"]
    response = await client.post(
        f"/api/tickets/{ticket['id']}/assign",
        json={"user_id": agent_id},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["assigned_to"] == agent_id
    assert response.json()["assigned_to_name"] == "Agente Demo"


async def test_dashboard_stats(client, make_ticket, admin_headers):
    await make_ticket()
    response = await client.get("/api/dashboard/stats", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["counts"]["open"] >= 1
    assert "sla_overdue" in body
    assert isinstance(body["recent"], list)
