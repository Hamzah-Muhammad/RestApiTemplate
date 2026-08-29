from fastapi.testclient import TestClient


def _other_user_headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/v1/auth/register",
        json={"email": "other@example.com", "full_name": "Other User", "password": "password123"},
    )
    response = client.post(
        "/v1/auth/login", data={"username": "other@example.com", "password": "password123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_and_get_project(client: TestClient, auth_headers: dict[str, str]) -> None:
    create = client.post(
        "/v1/projects",
        json={"name": "Website Redesign", "description": "Q3 project"},
        headers=auth_headers,
    )
    assert create.status_code == 201
    project_id = create.json()["id"]

    get = client.get(f"/v1/projects/{project_id}", headers=auth_headers)
    assert get.status_code == 200
    assert get.json()["name"] == "Website Redesign"


def test_list_projects_paginated(client: TestClient, auth_headers: dict[str, str]) -> None:
    for i in range(3):
        client.post("/v1/projects", json={"name": f"Project {i}"}, headers=auth_headers)

    response = client.get("/v1/projects?limit=2&offset=0", headers=auth_headers)
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["limit"] == 2


def test_update_project(client: TestClient, auth_headers: dict[str, str]) -> None:
    create = client.post("/v1/projects", json={"name": "Old Name"}, headers=auth_headers)
    project_id = create.json()["id"]

    update = client.patch(
        f"/v1/projects/{project_id}", json={"name": "New Name"}, headers=auth_headers
    )
    assert update.status_code == 200
    assert update.json()["name"] == "New Name"


def test_delete_project(client: TestClient, auth_headers: dict[str, str]) -> None:
    create = client.post("/v1/projects", json={"name": "To Delete"}, headers=auth_headers)
    project_id = create.json()["id"]

    delete = client.delete(f"/v1/projects/{project_id}", headers=auth_headers)
    assert delete.status_code == 204

    get = client.get(f"/v1/projects/{project_id}", headers=auth_headers)
    assert get.status_code == 404


def test_cannot_access_another_users_project(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    create = client.post("/v1/projects", json={"name": "Private"}, headers=auth_headers)
    project_id = create.json()["id"]

    other_headers = _other_user_headers(client)
    response = client.get(f"/v1/projects/{project_id}", headers=other_headers)
    assert response.status_code == 404


def test_projects_require_auth(client: TestClient) -> None:
    response = client.get("/v1/projects")
    assert response.status_code == 401
