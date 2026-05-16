import sqlite3
from pathlib import Path


def _topic_payload(assignment_id: int = 1) -> dict[str, object]:
    return {
        "assignment_id": assignment_id,
        "question": "Qual e o objetivo?",
        "response": "Explicar o tema.",
        "validated_response": "Explicar o tema com criterios.",
    }


def _topic_row(db_path: Path, topic_id: int):
    with sqlite3.connect(db_path) as connection:
        return connection.execute(
            """
            SELECT question, response, validated_response, active, deleted
            FROM topic
            WHERE id = ?
            """,
            (topic_id,),
        ).fetchone()


def test_topics_list_returns_only_active_records_with_pagination(api_client):
    client, _ = api_client

    response = client.get("/topics", params={"page": 2, "page_size": 1})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["page"] == 2
    assert data["page_size"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["question"] == "Pergunta 2"
    assert data["items"][0]["deleted"] is False


def test_topics_list_validates_query_params(api_client):
    client, _ = api_client

    invalid_page = client.get("/topics", params={"page": 0})
    invalid_page_size = client.get("/topics", params={"page_size": 101})

    assert invalid_page.status_code == 422
    assert invalid_page_size.status_code == 422


def test_topic_crud_and_soft_delete(api_client):
    client, db_path = api_client

    create = client.post("/topics", json=_topic_payload())
    topic_id = create.json()["id"]
    get_created = client.get(f"/topics/{topic_id}")
    update = client.put(
        f"/topics/{topic_id}",
        json={
            "question": "Pergunta atualizada",
            "response": "Resposta atualizada",
            "validated_response": "Resposta validada atualizada",
        },
    )
    delete = client.delete(f"/topics/{topic_id}")
    get_deleted = client.get(f"/topics/{topic_id}")

    assert create.status_code == 200
    assert create.json()["assignment_id"] == 1
    assert create.json()["active"] is True
    assert create.json()["deleted"] is False

    assert get_created.status_code == 200
    assert get_created.json()["id"] == topic_id

    assert update.status_code == 200
    assert update.json()["question"] == "Pergunta atualizada"
    assert update.json()["response"] == "Resposta atualizada"
    assert update.json()["validated_response"] == "Resposta validada atualizada"

    assert delete.status_code == 200
    assert delete.json()["active"] is False
    assert delete.json()["deleted"] is True
    assert get_deleted.status_code == 404
    assert _topic_row(db_path, topic_id) == (
        "Pergunta atualizada",
        "Resposta atualizada",
        "Resposta validada atualizada",
        0,
        1,
    )


def test_topic_endpoints_return_404_for_missing_records(api_client):
    client, _ = api_client

    get_missing = client.get("/topics/999")
    update_missing = client.put(
        "/topics/999",
        json={
            "question": "Pergunta",
            "response": "Resposta",
            "validated_response": "Resposta validada",
        },
    )
    delete_missing = client.delete("/topics/999")

    assert get_missing.status_code == 404
    assert update_missing.status_code == 404
    assert delete_missing.status_code == 404


def test_topic_create_requires_existing_active_assignment(api_client):
    client, _ = api_client

    missing_assignment = client.post("/topics", json=_topic_payload(assignment_id=999))
    deleted_assignment = client.post("/topics", json=_topic_payload(assignment_id=3))

    assert missing_assignment.status_code == 404
    assert deleted_assignment.status_code == 404


def test_topic_payload_validation(api_client):
    client, _ = api_client

    create_invalid = client.post("/topics", json={**_topic_payload(), "question": ""})
    update_invalid = client.put(
        "/topics/1",
        json={
            "question": "",
            "response": "Resposta",
            "validated_response": "Resposta validada",
        },
    )

    assert create_invalid.status_code == 422
    assert update_invalid.status_code == 422
