from fastapi.testclient import TestClient


def test_register_creates_user(client: TestClient) -> None:
    response = client.post(
        "/v1/auth/register",
        json={"email": "new@example.com", "full_name": "New User", "password": "password123"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert "id" in body
    assert "password" not in body


def test_register_duplicate_email_rejected(client: TestClient) -> None:
    payload = {"email": "dup@example.com", "full_name": "Dup User", "password": "password123"}
    client.post("/v1/auth/register", json=payload)
    response = client.post("/v1/auth/register", json=payload)
    assert response.status_code == 409


def test_login_success_returns_token(client: TestClient) -> None:
    client.post(
        "/v1/auth/register",
        json={"email": "login@example.com", "full_name": "Login User", "password": "password123"},
    )
    response = client.post(
        "/v1/auth/login", data={"username": "login@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_wrong_password_rejected(client: TestClient) -> None:
    client.post(
        "/v1/auth/register",
        json={"email": "wrong@example.com", "full_name": "Wrong User", "password": "password123"},
    )
    response = client.post(
        "/v1/auth/login", data={"username": "wrong@example.com", "password": "not-the-password"}
    )
    assert response.status_code == 401


def test_me_requires_token(client: TestClient) -> None:
    response = client.get("/v1/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"
