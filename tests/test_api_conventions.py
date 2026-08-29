"""Cross-cutting API conventions: versioning, error envelope, auth edge cases,
pagination clamping, query validation, readiness."""

from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient

from app.core.config import get_settings


def test_routes_are_versioned(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert client.get("/v1/projects", headers=auth_headers).status_code == 200
    # The unversioned path is not an alias - a future /v2 must not silently shadow it.
    assert client.get("/projects", headers=auth_headers).status_code == 404


def test_validation_error_uses_envelope(client: TestClient) -> None:
    response = client.post(
        "/v1/auth/register",
        json={"email": "not-an-email", "full_name": "X", "password": "short"},
    )
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["message"] == "Request validation failed"
    assert {d["field"] for d in error["details"]} == {"email", "password"}


def test_http_error_uses_envelope(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/v1/projects/999999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json() == {"error": {"code": "not_found", "message": "Project not found"}}


def test_garbage_token_rejected(client: TestClient) -> None:
    response = client.get("/v1/auth/me", headers={"Authorization": "Bearer not.a.jwt"})
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "unauthorized"


def test_expired_token_rejected(client: TestClient, auth_headers: dict[str, str]) -> None:
    settings = get_settings()
    user_id = client.get("/v1/auth/me", headers=auth_headers).json()["id"]
    expired = jwt.encode(
        {"sub": str(user_id), "exp": datetime.now(UTC) - timedelta(minutes=1)},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    response = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


def test_password_limited_to_72_bytes(client: TestClient) -> None:
    # 30 characters, but 120 bytes in UTF-8 - past bcrypt's limit.
    response = client.post(
        "/v1/auth/register",
        json={"email": "emoji@example.com", "full_name": "Emoji", "password": "🔑" * 30},
    )
    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == "password"


def test_pagination_limit_is_clamped(client: TestClient, auth_headers: dict[str, str]) -> None:
    too_big = client.get("/v1/projects?limit=500", headers=auth_headers).json()
    assert too_big["limit"] == 100
    too_small = client.get("/v1/projects?limit=0&offset=-5", headers=auth_headers).json()
    assert too_small["limit"] == 1
    assert too_small["offset"] == 0


def test_invalid_sort_field_rejected(client: TestClient, auth_headers: dict[str, str]) -> None:
    project_id = client.post("/v1/projects", json={"name": "P"}, headers=auth_headers).json()["id"]
    response = client.get(f"/v1/projects/{project_id}/tasks?sort_by=owner_id", headers=auth_headers)
    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == "sort_by"


def test_health_endpoints(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/health/ready").json() == {"status": "ok", "database": "ok"}
