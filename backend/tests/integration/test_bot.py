async def run(client, headers, command: str) -> str:
    response = await client.post(
        "/api/bot/command", json={"command": command}, headers=headers
    )
    assert response.status_code == 200, response.text
    return response.json()["reply"]


async def test_bot_requires_internal_role(client, tenant_headers, seeded):
    response = await client.post(
        "/api/bot/command", json={"command": "/chamados abertos"}, headers=tenant_headers
    )
    assert response.status_code == 403


async def test_bot_list_open(client, make_ticket, admin_headers):
    await make_ticket(title="Bot visible ticket")
    reply = await run(client, admin_headers, "/chamados abertos")
    assert "Open tickets" in reply
    assert "HD-" in reply


async def test_bot_view_and_status_flow(client, make_ticket, admin_headers):
    ticket = await make_ticket(title="Bot managed ticket")
    code = ticket["code"]

    view = await run(client, admin_headers, f"/ver {code}")
    assert "Bot managed ticket" in view
    assert "Status: open" in view

    status = await run(client, admin_headers, f"/status {code} em_analise")
    assert "Previous status: open" in status
    assert "New status: in_analysis" in status

    reply = await run(client, admin_headers, f"/responder {code} Estamos analisando.")
    assert "Reply sent" in reply

    resolve = await run(client, admin_headers, f"/resolver {code} Ajuste realizado.")
    assert "resolved" in resolve


async def test_bot_agent_cannot_change_priority(client, make_ticket, agent_headers):
    ticket = await make_ticket()
    reply = await run(client, agent_headers, f"/prioridade {ticket['code']} alta")
    assert "Only admins" in reply


async def test_bot_unknown_command_returns_help(client, admin_headers, seeded):
    reply = await run(client, admin_headers, "/naoexiste")
    assert "/ver" in reply


async def test_bot_unknown_ticket(client, admin_headers, seeded):
    reply = await run(client, admin_headers, "/ver HD-9999")
    assert "Error" in reply or "not found" in reply
