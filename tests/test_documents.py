import asyncio
import os
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from tortoise import Tortoise

os.environ.setdefault("SECRET_KEY", "test-secret-key-32-bytes-minimum-value")
os.environ.setdefault("REFRESH_SECRET_KEY", "test-refresh-secret-key-32-bytes-minimum-value")

from app.config.security import hash_password  # noqa: E402
from app.config.settings import settings  # noqa: E402
from app.config.tortoise import TORTOISE_ORM  # noqa: E402
from app.main import app  # noqa: E402
from app.models.assignment import Assignment  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services import document_service  # noqa: E402
from app.services.document_service import DOCX_MEDIA_TYPE  # noqa: E402
from app.services.storage import (  # noqa: E402
    LocalDocumentStorage,
    S3DocumentStorage,
    create_document_storage,
)


@pytest.fixture()
def document_client(tmp_path):
    db_path = tmp_path / "documents.sqlite3"
    old_connection = TORTOISE_ORM["connections"]["default"]
    old_settings = {
        "storage_backend": settings.storage_backend,
        "storage_local_dir": settings.storage_local_dir,
        "storage_bucket": settings.storage_bucket,
        "storage_region": settings.storage_region,
        "storage_endpoint_url": settings.storage_endpoint_url,
        "storage_access_key_id": settings.storage_access_key_id,
        "storage_secret_access_key": settings.storage_secret_access_key,
        "browser_backend_url": settings.browser_backend_url,
        "public_backend_url": settings.public_backend_url,
        "onlyoffice_url": settings.onlyoffice_url,
    }

    TORTOISE_ORM["connections"]["default"] = f"sqlite://{db_path.as_posix()}"
    settings.storage_backend = "local"
    settings.storage_local_dir = tmp_path / "storage" / "documents"
    settings.browser_backend_url = "http://browser.test"
    settings.public_backend_url = "http://public.test"
    settings.onlyoffice_url = "http://onlyoffice.test"

    asyncio.run(_prepare_db())
    with TestClient(app) as client:
        yield client, db_path, tmp_path
    asyncio.run(Tortoise.close_connections())

    TORTOISE_ORM["connections"]["default"] = old_connection
    for key, value in old_settings.items():
        setattr(settings, key, value)


async def _prepare_db():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    user = await User.create(
        email="user@example.com",
        hashed_password=hash_password("correct-password"),
        name="Test User",
    )
    await Assignment.create(title="Primeira atividade", user=user)
    await Tortoise.close_connections()


def _upload_document(
    client: TestClient,
    assignment_id: int = 1,
    filename: str = "atividade.docx",
    content: bytes = b"docx bytes",
):
    return client.post(
        f"/assignments/{assignment_id}/document",
        files={"file": (filename, content, DOCX_MEDIA_TYPE)},
    )


def _document_row(db_path: Path):
    with sqlite3.connect(db_path) as connection:
        return connection.execute(
            """
            SELECT uuid, original_name, filename, key, deleted
            FROM documentrecord
            """
        ).fetchone()


def test_upload_missing_assignment_returns_404(document_client):
    client, _, _ = document_client

    response = _upload_document(client, assignment_id=999)

    assert response.status_code == 404


def test_upload_rejects_non_docx_and_empty_file(document_client):
    client, _, _ = document_client

    invalid_type = _upload_document(client, filename="atividade.pdf")
    empty_file = _upload_document(client, content=b"")

    assert invalid_type.status_code == 400
    assert empty_file.status_code == 400


def test_upload_creates_record_and_saves_local_file(document_client):
    client, db_path, tmp_path = document_client

    response = _upload_document(client, filename="plano.docx", content=b"first")

    assert response.status_code == 201
    data = response.json()
    assert data["original_name"] == "plano.docx"
    assert data["editor_url"] == f"http://browser.test/documents/{data['id']}/config"

    document_id, original_name, filename, key, deleted = _document_row(db_path)
    assert document_id == data["id"]
    assert original_name == "plano.docx"
    assert key.startswith(document_id.replace("-", ""))
    assert deleted == 0
    assert (tmp_path / "storage" / "documents" / filename).read_bytes() == b"first"

    documents = client.get("/documents")
    assert documents.status_code == 200
    assert documents.json()[0]["download_url"] == (
        f"http://browser.test/documents/{document_id}/download"
    )


def test_second_upload_reuses_record_and_changes_onlyoffice_key(document_client):
    client, db_path, tmp_path = document_client
    first = _upload_document(client, filename="primeiro.docx", content=b"first")
    first_id, _, filename, first_key, _ = _document_row(db_path)

    second = _upload_document(client, filename="segundo.docx", content=b"second")
    second_id, original_name, second_filename, second_key, deleted = _document_row(
        db_path
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["id"] == first.json()["id"]
    assert second_id == first_id
    assert original_name == "segundo.docx"
    assert second_filename == filename
    assert second_key != first_key
    assert deleted == 0
    assert (tmp_path / "storage" / "documents" / filename).read_bytes() == b"second"


def test_editor_config_uses_non_api_onlyoffice_routes(document_client):
    client, _, _ = document_client
    document_id = _upload_document(client).json()["id"]

    response = client.get(f"/documents/{document_id}/config")

    assert response.status_code == 200
    data = response.json()
    assert data["documentServerUrl"] == "http://onlyoffice.test"
    assert data["config"]["document"]["url"] == (
        f"http://public.test/documents/{document_id}/download"
    )
    assert data["config"]["editorConfig"]["callbackUrl"] == (
        f"http://public.test/onlyoffice/callback/{document_id}"
    )
    assert "/api/" not in data["config"]["document"]["url"]
    assert "/api/" not in data["config"]["editorConfig"]["callbackUrl"]


def test_download_returns_saved_docx(document_client):
    client, _, _ = document_client
    document_id = _upload_document(client, content=b"download me").json()["id"]

    response = client.get(f"/documents/{document_id}/download")

    assert response.status_code == 200
    assert response.content == b"download me"
    assert response.headers["content-type"].startswith(DOCX_MEDIA_TYPE)


def test_onlyoffice_callback_ignores_unhandled_status(document_client):
    client, db_path, _ = document_client
    document_id = _upload_document(client, content=b"original").json()["id"]
    first_key = _document_row(db_path)[3]

    callback = client.post(
        f"/onlyoffice/callback/{document_id}",
        json={"status": 1, "url": "http://onlyoffice.test/file"},
    )
    download = client.get(f"/documents/{document_id}/download")

    assert callback.status_code == 200
    assert callback.json() == {"error": 0}
    assert download.content == b"original"
    assert _document_row(db_path)[3] == first_key


def test_onlyoffice_callback_saves_edited_file_and_changes_key(
    document_client,
    monkeypatch,
):
    client, db_path, _ = document_client
    document_id = _upload_document(client, content=b"original").json()["id"]
    first_key = _document_row(db_path)[3]

    async def fake_download_callback_file(url: str) -> bytes:
        assert url == "http://onlyoffice.test/edited"
        return b"edited"

    monkeypatch.setattr(
        document_service,
        "download_callback_file",
        fake_download_callback_file,
    )

    callback = client.post(
        f"/onlyoffice/callback/{document_id}",
        json={"status": 2, "url": "http://onlyoffice.test/edited"},
    )
    download = client.get(f"/documents/{document_id}/download")

    assert callback.status_code == 200
    assert callback.json() == {"error": 0}
    assert download.content == b"edited"
    assert _document_row(db_path)[3] != first_key


def test_storage_factory_selects_local_s3_and_minio(tmp_path):
    old_settings = {
        "storage_backend": settings.storage_backend,
        "storage_local_dir": settings.storage_local_dir,
        "storage_bucket": settings.storage_bucket,
        "storage_region": settings.storage_region,
        "storage_endpoint_url": settings.storage_endpoint_url,
        "storage_access_key_id": settings.storage_access_key_id,
        "storage_secret_access_key": settings.storage_secret_access_key,
    }
    settings.storage_local_dir = tmp_path / "documents"
    settings.storage_bucket = "bucket"
    settings.storage_region = "us-east-1"
    settings.storage_access_key_id = "access"
    settings.storage_secret_access_key = "secret"

    try:
        settings.storage_backend = "local"
        assert isinstance(create_document_storage(), LocalDocumentStorage)

        settings.storage_backend = "s3"
        settings.storage_endpoint_url = None
        assert isinstance(create_document_storage(), S3DocumentStorage)

        settings.storage_backend = "minio"
        settings.storage_endpoint_url = "http://localhost:9000"
        assert isinstance(create_document_storage(), S3DocumentStorage)
    finally:
        for key, value in old_settings.items():
            setattr(settings, key, value)
