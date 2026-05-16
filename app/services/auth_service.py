from datetime import UTC, datetime

from fastapi import Request
from tortoise.exceptions import IntegrityError

from app.config.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    hash_password,
    decode_refresh_token,
    hash_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User


class InvalidCredentialsError(Exception):
    pass


class InactiveUserError(Exception):
    pass


class InvalidRefreshTokenError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass


async def register_user(email: str, password: str, name: str | None = None) -> User:
    normalized_email = email.lower()
    existing_user = await User.get_or_none(email=normalized_email)
    if existing_user is not None:
        raise UserAlreadyExistsError

    try:
        return await User.create(
            email=normalized_email,
            hashed_password=hash_password(password),
            name=name,
        )
    except IntegrityError as exc:
        raise UserAlreadyExistsError from exc


async def authenticate_user(email: str, password: str) -> User | None:
    user = await User.get_or_none(email=email.lower())
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def issue_token_pair(user: User, request: Request | None = None) -> dict:
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    await _store_refresh_token(user, refresh_token, request)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


async def refresh_token_pair(refresh_token: str, request: Request | None = None) -> dict:
    payload = _decode_refresh_or_raise(refresh_token)
    token_record = await _get_refresh_token_record(payload["jti"], refresh_token)
    if token_record is None:
        raise InvalidRefreshTokenError

    if token_record.revoked_at is not None:
        await _revoke_token_family(token_record.user_id, token_record.token_family)
        raise InvalidRefreshTokenError

    if _is_expired(token_record.expires_at):
        await _revoke_refresh_token_record(token_record)
        raise InvalidRefreshTokenError

    if not token_record.user.is_active:
        raise InactiveUserError

    new_refresh_token = create_refresh_token(
        token_record.user_id,
        token_family=token_record.token_family,
    )
    new_payload = decode_refresh_token(new_refresh_token)

    now = datetime.now(UTC)
    token_record.revoked_at = now
    token_record.replaced_by_jti = new_payload["jti"]
    await token_record.save(update_fields=["revoked_at", "replaced_by_jti"])

    await _store_refresh_token(token_record.user, new_refresh_token, request)
    return {
        "access_token": create_access_token(token_record.user_id),
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


async def revoke_refresh_token(refresh_token: str) -> None:
    payload = _decode_refresh_or_raise(refresh_token)
    token_record = await _get_refresh_token_record(payload["jti"], refresh_token)
    if token_record is None:
        raise InvalidRefreshTokenError
    await _revoke_refresh_token_record(token_record)


async def revoke_all_user_refresh_tokens(user_id: int) -> None:
    await RefreshToken.filter(
        user_id=user_id,
        revoked_at=None,
        expires_at__gt=datetime.now(UTC),
    ).update(revoked_at=datetime.now(UTC))


async def _store_refresh_token(
    user: User,
    refresh_token: str,
    request: Request | None,
) -> RefreshToken:
    payload = decode_refresh_token(refresh_token)
    expires_at = datetime.fromtimestamp(payload["exp"], UTC)
    user_agent = request.headers.get("user-agent") if request else None
    ip_address = request.client.host if request and request.client else None
    return await RefreshToken.create(
        user=user,
        jti=payload["jti"],
        token_hash=hash_token(refresh_token),
        token_family=payload["family"],
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
    )


async def _get_refresh_token_record(
    jti: str,
    refresh_token: str,
) -> RefreshToken | None:
    token_hash = hash_token(refresh_token)
    return (
        await RefreshToken.filter(jti=jti, token_hash=token_hash)
        .select_related("user")
        .first()
    )


async def _revoke_refresh_token_record(token_record: RefreshToken) -> None:
    if token_record.revoked_at is not None:
        return
    token_record.revoked_at = datetime.now(UTC)
    await token_record.save(update_fields=["revoked_at"])


async def _revoke_token_family(user_id: int, token_family: str) -> None:
    await RefreshToken.filter(
        user_id=user_id,
        token_family=token_family,
        revoked_at=None,
    ).update(revoked_at=datetime.now(UTC))


def _decode_refresh_or_raise(refresh_token: str) -> dict:
    try:
        return decode_refresh_token(refresh_token)
    except TokenError as exc:
        raise InvalidRefreshTokenError from exc


def _is_expired(expires_at: datetime) -> bool:
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at <= datetime.now(UTC)
