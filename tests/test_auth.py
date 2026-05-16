import asyncio
from datetime import UTC, datetime, timedelta
import os
import sqlite3

import jwt
import pytest
from fastapi.testclient import TestClient
from tortoise import Tortoise

os.environ.setdefault("SECRET_KEY", "test-secret-key-32-bytes-minimum-value")
os.environ.setdefault("REFRESH_SECRET_KEY", "test-refresh-secret-key-32-bytes-minimum-value")

from app.config.security import (  # noqa: E402
    create_refresh_token,
    hash_password,
    hash_token,
)
from app.config.settings import settings  # noqa: E402
from app.config.tortoise import TORTOISE_ORM  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402


@pytest.fixture()
def auth_client(tmp_path):
    db_path = tmp_path / "auth.sqlite3"
    TORTOISE_ORM["connections"]["default"] = f"sqlite://{db_path.as_posix()}"
    asyncio.run(_prepare_db())
    with TestClient(app) as client:
        yield client, db_path
    asyncio.run(Tortoise.close_connections())


async def _prepare_db():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    await User.create(
        email="user@example.com",
        hashed_password=hash_password("correct-password"),
        name="Test User",
    )
    await User.create(
        email="inactive@example.com",
        hashed_password=hash_password("correct-password"),
        name="Inactive User",
        is_active=False,
    )
    await Tortoise.close_connections()


def _login(client: TestClient, email: str = "user@example.com") -> dict:
    response = client.post(
        "/auth/login",
        json={"email": email, "password": "correct-password"},
    )
    assert response.status_code == 200
    return response.json()


def _register(client: TestClient, email: str = "new@example.com") -> dict:
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "new-password",
            "name": "New User",
        },
    )
    assert response.status_code == 201
    return response.json()


def _expired_access_token(user_id: int = 1) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user_id),
            "type": "access",
            "iat": now - timedelta(minutes=30),
            "exp": now - timedelta(minutes=1),
        },
        settings.require_secret_key(),
        algorithm=settings.jwt_algorithm,
    )


def _expired_refresh_token(user_id: int = 1) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user_id),
            "type": "refresh",
            "iat": now - timedelta(days=8),
            "exp": now - timedelta(days=1),
            "jti": "expired-jti",
        },
        settings.require_refresh_secret_key(),
        algorithm=settings.jwt_algorithm,
    )


def test_login_valid_returns_tokens_and_does_not_store_plain_refresh_token(auth_client):
    client, db_path = auth_client
    data = _login(client)

    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]

    with sqlite3.connect(db_path) as connection:
        token_hash = connection.execute(
            "SELECT token_hash FROM refreshtoken"
        ).fetchone()[0]

    assert token_hash == hash_token(data["refresh_token"])
    assert token_hash != data["refresh_token"]


def test_register_creates_user_returns_tokens_and_hashes_password(auth_client):
    client, db_path = auth_client
    data = _register(client)

    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]

    me = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "new@example.com"

    with sqlite3.connect(db_path) as connection:
        hashed_password = connection.execute(
            "SELECT hashed_password FROM user WHERE email = ?",
            ("new@example.com",),
        ).fetchone()[0]

    assert hashed_password != "new-password"


def test_register_duplicate_email_returns_409(auth_client):
    client, _ = auth_client
    response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "new-password",
            "name": "Duplicate User",
        },
    )

    assert response.status_code == 409


def test_register_short_password_returns_422(auth_client):
    client, _ = auth_client
    response = client.post(
        "/auth/register",
        json={"email": "short@example.com", "password": "short"},
    )

    assert response.status_code == 422


def test_login_invalid_returns_generic_401(auth_client):
    client, _ = auth_client
    wrong_email = client.post(
        "/auth/login",
        json={"email": "missing@example.com", "password": "correct-password"},
    )
    wrong_password = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "wrong-password"},
    )

    assert wrong_email.status_code == 401
    assert wrong_password.status_code == 401
    assert wrong_email.json() == wrong_password.json()


def test_login_inactive_user_returns_403(auth_client):
    client, _ = auth_client
    response = client.post(
        "/auth/login",
        json={"email": "inactive@example.com", "password": "correct-password"},
    )

    assert response.status_code == 403


def test_auth_me_requires_valid_access_token(auth_client):
    client, _ = auth_client
    tokens = _login(client)

    valid = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    missing = client.get("/auth/me")
    invalid = client.get("/auth/me", headers={"Authorization": "Bearer invalid"})
    expired = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {_expired_access_token()}"},
    )
    refresh_as_access = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
    )

    assert valid.status_code == 200
    assert valid.json()["email"] == "user@example.com"
    assert missing.status_code == 401
    assert invalid.status_code == 401
    assert expired.status_code == 401
    assert refresh_as_access.status_code == 401


def test_refresh_rotates_token_and_rejects_old_refresh(auth_client):
    client, _ = auth_client
    tokens = _login(client)

    refreshed = client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    old_reused = client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    access_as_refresh = client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["access_token"]},
    )

    assert refreshed.status_code == 200
    assert refreshed.json()["refresh_token"] != tokens["refresh_token"]
    assert old_reused.status_code == 401
    assert access_as_refresh.status_code == 401


def test_refresh_expired_token_returns_401(auth_client):
    client, _ = auth_client
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": _expired_refresh_token()},
    )

    assert response.status_code == 401


def test_logout_revokes_refresh_token(auth_client):
    client, _ = auth_client
    tokens = _login(client)

    logout = client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    refresh = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert logout.status_code == 204
    assert refresh.status_code == 401


def test_logout_all_revokes_all_user_refresh_tokens(auth_client):
    client, _ = auth_client
    first = _login(client)
    second = _login(client)

    logout_all = client.post(
        "/auth/logout-all",
        headers={"Authorization": f"Bearer {first['access_token']}"},
    )
    first_refresh = client.post(
        "/auth/refresh",
        json={"refresh_token": first["refresh_token"]},
    )
    second_refresh = client.post(
        "/auth/refresh",
        json={"refresh_token": second["refresh_token"]},
    )

    assert logout_all.status_code == 204
    assert first_refresh.status_code == 401
    assert second_refresh.status_code == 401


def test_tokens_contain_required_claims(auth_client):
    client, _ = auth_client
    tokens = _login(client)

    access_payload = jwt.decode(
        tokens["access_token"],
        settings.require_secret_key(),
        algorithms=[settings.jwt_algorithm],
    )
    refresh_payload = jwt.decode(
        tokens["refresh_token"],
        settings.require_refresh_secret_key(),
        algorithms=[settings.jwt_algorithm],
    )

    assert access_payload["type"] == "access"
    assert access_payload["exp"]
    assert refresh_payload["type"] == "refresh"
    assert refresh_payload["exp"]
    assert refresh_payload["jti"]


def test_created_refresh_token_has_jti_claim(auth_client):
    client, _ = auth_client
    tokens = _login(client)
    refresh_payload = jwt.decode(
        tokens["refresh_token"],
        settings.require_refresh_secret_key(),
        algorithms=[settings.jwt_algorithm],
    )

    assert create_refresh_token(refresh_payload["sub"])
    assert refresh_payload["jti"]
