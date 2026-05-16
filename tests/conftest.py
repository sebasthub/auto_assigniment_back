import asyncio
import os

import pytest
from fastapi.testclient import TestClient
from tortoise import Tortoise

os.environ.setdefault("SECRET_KEY", "test-secret-key-32-bytes-minimum-value")
os.environ.setdefault("REFRESH_SECRET_KEY", "test-refresh-secret-key-32-bytes-minimum-value")

from app.config.settings import settings  # noqa: E402
from app.config.tortoise import TORTOISE_ORM  # noqa: E402
from app.main import app  # noqa: E402
from app.models.assignment import Assignment  # noqa: E402
from app.models.topic import Topic  # noqa: E402


@pytest.fixture()
def api_client(tmp_path):
    db_path = tmp_path / "api.sqlite3"
    old_connection = TORTOISE_ORM["connections"]["default"]
    old_settings = {
        "storage_backend": settings.storage_backend,
        "storage_local_dir": settings.storage_local_dir,
    }

    TORTOISE_ORM["connections"]["default"] = f"sqlite://{db_path.as_posix()}"
    settings.storage_backend = "local"
    settings.storage_local_dir = tmp_path / "storage" / "documents"

    asyncio.run(_prepare_db())
    with TestClient(app) as client:
        yield client, db_path
    asyncio.run(Tortoise.close_connections())

    TORTOISE_ORM["connections"]["default"] = old_connection
    for key, value in old_settings.items():
        setattr(settings, key, value)


async def _prepare_db():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    first = await Assignment.create(title="Primeira atividade")
    second = await Assignment.create(title="Segunda atividade")
    await Assignment.create(title="Atividade removida", active=False, deleted=True)
    await Topic.create(
        assignment=first,
        question="Pergunta 1",
        response="Resposta 1",
        validated_response="Resposta validada 1",
    )
    await Topic.create(
        assignment=first,
        question="Pergunta 2",
        response="Resposta 2",
        validated_response="Resposta validada 2",
    )
    await Topic.create(
        assignment=second,
        question="Pergunta removida",
        response="Resposta removida",
        validated_response="Resposta validada removida",
        active=False,
        deleted=True,
    )
    await Tortoise.close_connections()
