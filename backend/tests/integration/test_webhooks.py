import uuid

from tests.integration.conftest import WEBHOOK_HEADERS


async def test_webhook_requires_token(client, seeded):
    response = await client.post("/api/webhooks/generic", json={"message": "hi"})
    assert response.status_code == 401


async def test_generic_webhook_creates_ticket(client, admin_headers, seeded):
    external_id = f"evt-{uuid.uuid4().hex[:8]}"
    payload = {
        "tenant_slug": "demo-telecom",
        "external_id": external_id,
        "name": "Novo Contato",
        "email": "novo@demo.com",
        "message": "Erro ao gerar boleto na plataforma.",
        "title": "Erro ao gerar boleto",
    }
    response = await client.post(
        "/api/webhooks/generic", json=payload, headers=WEBHOOK_HEADERS
    )
    assert response.status_code == 202, response.text
    body = response.json()
    assert body["created"] is True
    assert body["ticket_code"].startswith("HD-")

    detail = await client.get(
        f"/api/tickets/{body['ticket_id']}", headers=admin_headers
    )
    ticket = detail.json()
    assert ticket["source_channel"] == "webhook"
    assert ticket["requester"]["email"] == "novo@demo.com"


async def test_duplicate_external_id_is_ignored(client, seeded):
    external_id = f"evt-{uuid.uuid4().hex[:8]}"
    payload = {
        "tenant_slug": "demo-telecom",
        "external_id": external_id,
        "name": "Dup Sender",
        "email": "dup@demo.com",
        "message": "Mensagem duplicada",
    }
    first = await client.post("/api/webhooks/generic", json=payload, headers=WEBHOOK_HEADERS)
    assert first.json()["duplicate"] is False
    second = await client.post("/api/webhooks/generic", json=payload, headers=WEBHOOK_HEADERS)
    assert second.json()["duplicate"] is True


async def test_followup_message_lands_on_same_ticket(client, admin_headers, seeded):
    phone = "+5571900001111"
    first = await client.post(
        "/api/webhooks/whatsapp",
        json={"tenant_slug": "demo-telecom", "from": phone, "name": "Seq Sender",
              "message": "Primeiro problema relatado", "id": f"wa-{uuid.uuid4().hex[:8]}"},
        headers=WEBHOOK_HEADERS,
    )
    assert first.json()["created"] is True
    ticket_id = first.json()["ticket_id"]

    followup = await client.post(
        "/api/webhooks/whatsapp",
        json={"from": phone, "name": "Seq Sender",
              "message": "Complemento do problema", "id": f"wa-{uuid.uuid4().hex[:8]}"},
        headers=WEBHOOK_HEADERS,
    )
    assert followup.json()["created"] is False
    assert followup.json()["ticket_id"] == ticket_id

    messages = await client.get(
        f"/api/tickets/{ticket_id}/messages", headers=admin_headers
    )
    assert len(messages.json()) >= 2


async def test_unknown_tenant_is_rejected(client, seeded):
    response = await client.post(
        "/api/webhooks/generic",
        json={"name": "Ghost", "email": "ghost@nowhere.com", "message": "hello"},
        headers=WEBHOOK_HEADERS,
    )
    assert response.status_code == 422


async def test_whatsapp_cloud_api_shape(client, seeded):
    wamid = f"wamid.{uuid.uuid4().hex[:10]}"
    payload = {
        "tenant_slug": "demo-telecom",
        "entry": [{"changes": [{"value": {
            "contacts": [{"profile": {"name": "Carlos Silva"}, "wa_id": "5571999999999"}],
            "messages": [{"id": wamid, "from": "5571999999999",
                          "text": {"body": "Problema via Cloud API"}}],
        }}]}],
    }
    response = await client.post(
        "/api/webhooks/whatsapp", json=payload, headers=WEBHOOK_HEADERS
    )
    assert response.status_code == 202
    assert response.json()["ticket_code"].startswith("HD-")


async def test_demo_simulator(client, admin_headers, seeded):
    response = await client.post(
        "/api/demo/simulate-whatsapp-message",
        json={"tenant_slug": "demo-telecom", "name": "Simulado",
              "phone": "+5571912340000", "message": "Chamado simulado via demo"},
    )
    assert response.status_code == 200
    assert response.json()["ticket_code"].startswith("HD-")
