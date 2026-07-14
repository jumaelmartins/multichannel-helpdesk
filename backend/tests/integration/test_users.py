async def test_admin_lists_internal_users(client, admin_headers):
    response = await client.get("/api/users", headers=admin_headers)
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 2
    roles = {u["role"] for u in users}
    assert roles <= {"admin", "agent"}
    assert all("password_hash" not in u for u in users)


async def test_agent_lists_internal_users_for_assignment_display(client, agent_headers):
    response = await client.get("/api/users", headers=agent_headers)
    assert response.status_code == 200


async def test_tenant_user_cannot_list_users(client, tenant_headers):
    response = await client.get("/api/users", headers=tenant_headers)
    assert response.status_code == 403
