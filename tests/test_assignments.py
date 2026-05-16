import sqlite3
from pathlib import Path


def _assignment_payload(title: str = "Nova atividade") -> dict[str, str]:
    return {"title": title}


def _auth_headers(client, email: str = "user@example.com") -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"email": email, "password": "correct-password"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _assignment_row(db_path: Path, assignment_id: int):
    with sqlite3.connect(db_path) as connection:
        return connection.execute(
            "SELECT title, active, deleted, user_id FROM assignment WHERE id = ?",
            (assignment_id,),
        ).fetchone()


def test_assignments_list_returns_only_active_records_with_pagination(api_client):
    client, _ = api_client
    headers = _auth_headers(client)

    response = client.get(
        "/assignments",
        params={"page": 1, "page_size": 1},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["page"] == 1
    assert data["page_size"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Primeira atividade"
    assert data["items"][0]["deleted"] is False


def test_assignments_list_returns_only_current_user_records(api_client):
    client, _ = api_client
    other_headers = _auth_headers(client, email="other@example.com")

    response = client.get("/assignments", headers=other_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert [item["title"] for item in data["items"]] == [
        "Atividade de outro usuario"
    ]


def test_assignments_require_authentication(api_client):
    client, _ = api_client

    list_response = client.get("/assignments")
    create_response = client.post("/assignments", json=_assignment_payload())
    get_response = client.get("/assignments/1")
    update_response = client.put("/assignments/1", json=_assignment_payload())
    delete_response = client.delete("/assignments/1")

    assert list_response.status_code == 401
    assert create_response.status_code == 401
    assert get_response.status_code == 401
    assert update_response.status_code == 401
    assert delete_response.status_code == 401


def test_assignments_list_validates_query_params(api_client):
    client, _ = api_client
    headers = _auth_headers(client)

    invalid_page = client.get("/assignments", params={"page": 0}, headers=headers)
    invalid_page_size = client.get(
        "/assignments",
        params={"page_size": 101},
        headers=headers,
    )

    assert invalid_page.status_code == 422
    assert invalid_page_size.status_code == 422


def test_assignment_crud_and_soft_delete(api_client):
    client, db_path = api_client
    headers = _auth_headers(client)

    create = client.post(
        "/assignments",
        json=_assignment_payload("Trabalho final"),
        headers=headers,
    )
    assignment_id = create.json()["id"]
    get_created = client.get(f"/assignments/{assignment_id}", headers=headers)
    update = client.put(
        f"/assignments/{assignment_id}",
        json=_assignment_payload("Trabalho final revisado"),
        headers=headers,
    )
    delete = client.delete(f"/assignments/{assignment_id}", headers=headers)
    get_deleted = client.get(f"/assignments/{assignment_id}", headers=headers)

    assert create.status_code == 200
    assert create.json()["title"] == "Trabalho final"
    assert create.json()["active"] is True
    assert create.json()["deleted"] is False
    assert create.json()["topics"] == []
    assert create.json()["document_record"] is None

    assert get_created.status_code == 200
    assert get_created.json()["id"] == assignment_id

    assert update.status_code == 200
    assert update.json()["title"] == "Trabalho final revisado"

    assert delete.status_code == 200
    assert delete.json()["active"] is False
    assert delete.json()["deleted"] is True
    assert get_deleted.status_code == 404
    assert _assignment_row(db_path, assignment_id) == (
        "Trabalho final revisado",
        0,
        1,
        1,
    )


def test_assignment_detail_update_and_delete_do_not_cross_users(api_client):
    client, _ = api_client
    other_headers = _auth_headers(client, email="other@example.com")

    get_response = client.get("/assignments/1", headers=other_headers)
    update_response = client.put(
        "/assignments/1",
        json=_assignment_payload("Tentativa externa"),
        headers=other_headers,
    )
    delete_response = client.delete("/assignments/1", headers=other_headers)

    assert get_response.status_code == 404
    assert update_response.status_code == 404
    assert delete_response.status_code == 404


def test_assignment_endpoints_return_404_for_missing_records(api_client):
    client, _ = api_client
    headers = _auth_headers(client)

    get_missing = client.get("/assignments/999", headers=headers)
    update_missing = client.put(
        "/assignments/999",
        json=_assignment_payload(),
        headers=headers,
    )
    delete_missing = client.delete("/assignments/999", headers=headers)

    assert get_missing.status_code == 404
    assert update_missing.status_code == 404
    assert delete_missing.status_code == 404


def test_assignment_payload_validation(api_client):
    client, _ = api_client
    headers = _auth_headers(client)

    create_invalid = client.post("/assignments", json={"title": ""}, headers=headers)
    update_invalid = client.put("/assignments/1", json={"title": ""}, headers=headers)

    assert create_invalid.status_code == 422
    assert update_invalid.status_code == 422


def test_get_assignment_includes_active_topics(api_client):
    client, _ = api_client
    headers = _auth_headers(client)

    response = client.get("/assignments/1", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert [topic["question"] for topic in data["topics"]] == [
        "Pergunta 1",
        "Pergunta 2",
    ]


def test_deleting_assignment_soft_deletes_its_topics(api_client):
    client, db_path = api_client
    headers = _auth_headers(client)

    response = client.delete("/assignments/1", headers=headers)

    assert response.status_code == 200
    with sqlite3.connect(db_path) as connection:
        topic_flags = connection.execute(
            "SELECT active, deleted FROM topic WHERE assignment_id = 1 ORDER BY id"
        ).fetchall()
    assert topic_flags == [(0, 1), (0, 1)]
    assert client.get("/topics/1").status_code == 404
