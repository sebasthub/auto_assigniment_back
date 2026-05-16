import sqlite3
from pathlib import Path


def _assignment_payload(title: str = "Nova atividade") -> dict[str, str]:
    return {"title": title}


def _assignment_row(db_path: Path, assignment_id: int):
    with sqlite3.connect(db_path) as connection:
        return connection.execute(
            "SELECT title, active, deleted FROM assignment WHERE id = ?",
            (assignment_id,),
        ).fetchone()


def test_assignments_list_returns_only_active_records_with_pagination(api_client):
    client, _ = api_client

    response = client.get("/assignments", params={"page": 1, "page_size": 1})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["page"] == 1
    assert data["page_size"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Primeira atividade"
    assert data["items"][0]["deleted"] is False


def test_assignments_list_validates_query_params(api_client):
    client, _ = api_client

    invalid_page = client.get("/assignments", params={"page": 0})
    invalid_page_size = client.get("/assignments", params={"page_size": 101})

    assert invalid_page.status_code == 422
    assert invalid_page_size.status_code == 422


def test_assignment_crud_and_soft_delete(api_client):
    client, db_path = api_client

    create = client.post("/assignments", json=_assignment_payload("Trabalho final"))
    assignment_id = create.json()["id"]
    get_created = client.get(f"/assignments/{assignment_id}")
    update = client.put(
        f"/assignments/{assignment_id}",
        json=_assignment_payload("Trabalho final revisado"),
    )
    delete = client.delete(f"/assignments/{assignment_id}")
    get_deleted = client.get(f"/assignments/{assignment_id}")

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
    )


def test_assignment_endpoints_return_404_for_missing_records(api_client):
    client, _ = api_client

    get_missing = client.get("/assignments/999")
    update_missing = client.put("/assignments/999", json=_assignment_payload())
    delete_missing = client.delete("/assignments/999")

    assert get_missing.status_code == 404
    assert update_missing.status_code == 404
    assert delete_missing.status_code == 404


def test_assignment_payload_validation(api_client):
    client, _ = api_client

    create_invalid = client.post("/assignments", json={"title": ""})
    update_invalid = client.put("/assignments/1", json={"title": ""})

    assert create_invalid.status_code == 422
    assert update_invalid.status_code == 422


def test_get_assignment_includes_active_topics(api_client):
    client, _ = api_client

    response = client.get("/assignments/1")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert [topic["question"] for topic in data["topics"]] == [
        "Pergunta 1",
        "Pergunta 2",
    ]


def test_deleting_assignment_soft_deletes_its_topics(api_client):
    client, db_path = api_client

    response = client.delete("/assignments/1")

    assert response.status_code == 200
    with sqlite3.connect(db_path) as connection:
        topic_flags = connection.execute(
            "SELECT active, deleted FROM topic WHERE assignment_id = 1 ORDER BY id"
        ).fetchall()
    assert topic_flags == [(0, 1), (0, 1)]
    assert client.get("/topics/1").status_code == 404
