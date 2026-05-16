from fastapi import Response

from app.config.settings import settings

ACCESS_TOKEN_COOKIE = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    secure = settings.is_production
    response.set_cookie(
        ACCESS_TOKEN_COOKIE,
        access_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
        max_age=settings.access_token_expire_minutes * 60,
    )
    response.set_cookie(
        REFRESH_TOKEN_COOKIE,
        refresh_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/auth/refresh",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_TOKEN_COOKIE, path="/")
    response.delete_cookie(REFRESH_TOKEN_COOKIE, path="/auth/refresh")
