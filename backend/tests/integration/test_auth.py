async def test_login_success(client, seeded):
    response = await client.post(
        "/api/auth/login", json={"email": "admin@demo.com", "password": "demo123"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["user"]["email"] == "admin@demo.com"
    assert "password_hash" not in body["user"]


async def test_login_wrong_password(client, seeded):
    response = await client.post(
        "/api/auth/login", json={"email": "admin@demo.com", "password": "wrong"}
    )
    assert response.status_code == 401


async def test_me(client, admin_headers):
    response = await client.get("/api/auth/me", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


async def test_refresh(client, seeded):
    login = await client.post(
        "/api/auth/login", json={"email": "agent@demo.com", "password": "demo123"}
    )
    refresh_token = login.json()["refresh_token"]
    response = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert response.json()["access_token"]


async def test_protected_route_requires_token(client, seeded):
    response = await client.get("/api/tickets")
    assert response.status_code == 401
