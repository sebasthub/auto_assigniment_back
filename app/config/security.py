from datetime import UTC, datetime, timedelta
import hashlib
from uuid import uuid4

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError as PyJWTInvalidTokenError
from pwdlib import PasswordHash

from app.config.settings import settings

password_hash = PasswordHash.recommended()


class TokenError(ValueError):
    pass


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(
    subject: str | int,
    extra_claims: dict | None = None,
) -> str:
    now = datetime.now(UTC)
    claims = dict(extra_claims or {})
    claims.update(
        {
            "sub": str(subject),
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        }
    )
    return jwt.encode(claims, settings.require_secret_key(), algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str | int, token_family: str | None = None) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": str(subject),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=settings.refresh_token_expire_days),
        "jti": str(uuid4()),
        "family": token_family or str(uuid4()),
    }
    return jwt.encode(
        claims,
        settings.require_refresh_secret_key(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict:
    payload = _decode_token(token, settings.require_secret_key())
    if payload.get("type") != "access":
        raise TokenError("Invalid access token type")
    return payload


def decode_refresh_token(token: str) -> dict:
    payload = _decode_token(token, settings.require_refresh_secret_key())
    if payload.get("type") != "refresh":
        raise TokenError("Invalid refresh token type")
    if not payload.get("jti"):
        raise TokenError("Refresh token missing jti")
    return payload


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _decode_token(token: str, secret: str) -> dict:
    try:
        return jwt.decode(token, secret, algorithms=[settings.jwt_algorithm])
    except ExpiredSignatureError as exc:
        raise TokenError("Token expired") from exc
    except PyJWTInvalidTokenError as exc:
        raise TokenError("Invalid token") from exc
