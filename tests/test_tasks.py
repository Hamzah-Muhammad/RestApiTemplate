from fastapi.testclient import TestClient


def _create_project(client: TestClient, headers: dict[str, str]) -> int:
    response = client.post("/projects", json={"name": "Task Project"}, headers=headers)
    return response.json()["id"]


def test_create_and_list_tasks(client: TestClient, auth_headers: dict[str, str]) -> None:
    project_id = _create_project(client, auth_headers)

    create = client.post(
        f"/projects/{project_id}/tasks", json={"title": "Write tests"}, headers=auth_headers
    )
    assert create.status_code == 201
    assert create.json()["status"] == "todo"

    listing = client.get(f"/projects/{project_id}/tasks", headers=auth_headers)
    assert listing.json()["total"] == 1


def test_filter_tasks_by_status(client: TestClient, auth_headers: dict[str, str]) -> None:
    project_id = _create_project(client, auth_headers)
    client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Todo task", "status": "todo"},
        headers=auth_headers,
    )
    client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Done task", "status": "done"},
        headers=auth_headers,
    )

    response = client.get(f"/projects/{project_id}/tasks?status=done", headers=auth_headers)
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Done task"


def test_sort_tasks_by_title_ascending(client: TestClient, auth_headers: dict[str, str]) -> None:
    project_id = _create_project(client, auth_headers)
    for title in ["Charlie", "Alpha", "Bravo"]:
        client.post(f"/projects/{project_id}/tasks", json={"title": title}, headers=auth_headers)

    response = client.get(
        f"/projects/{project_id}/tasks?sort_by=title&sort_dir=asc", headers=auth_headers
    )
    titles = [item["title"] for item in response.json()["items"]]
    assert titles == ["Alpha", "Bravo", "Charlie"]


def test_update_task_status(client: TestClient, auth_headers: dict[str, str]) -> None:
    project_id = _create_project(client, auth_headers)
    create = client.post(
        f"/projects/{project_id}/tasks", json={"title": "Ship it"}, headers=auth_headers
    )
    task_id = create.json()["id"]

    update = client.patch(
        f"/tasks/{task_id}", json={"status": "in_progress"}, headers=auth_headers
    )
    assert update.status_code == 200
    assert update.json()["status"] == "in_progress"


def test_delete_task(client: TestClient, auth_headers: dict[str, str]) -> None:
    project_id = _create_project(client, auth_headers)
    create = client.post(
        f"/projects/{project_id}/tasks", json={"title": "Temp"}, headers=auth_headers
    )
    task_id = create.json()["id"]

    delete = client.delete(f"/tasks/{task_id}", headers=auth_headers)
    assert delete.status_code == 204

    get = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert get.status_code == 404


def test_cannot_create_task_in_another_users_project(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    project_id = _create_project(client, auth_headers)

    client.post(
        "/auth/register",
        json={
            "email": "intruder@example.com",
            "full_name": "Intruder",
            "password": "password123",
        },
    )
    login = client.post(
        "/auth/login", data={"username": "intruder@example.com", "password": "password123"}
    )
    intruder_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = client.post(
        f"/projects/{project_id}/tasks", json={"title": "Sneaky"}, headers=intruder_headers
    )
    assert response.status_code == 404
