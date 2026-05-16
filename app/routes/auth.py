from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RegisterRequest,
    RefreshRequest,
    TokenResponse,
    UserMeResponse,
)
from app.services.auth_service import (
    InactiveUserError,
    InvalidRefreshTokenError,
    UserAlreadyExistsError,
    authenticate_user,
    issue_token_pair,
    refresh_token_pair,
    register_user,
    revoke_all_user_refresh_tokens,
    revoke_refresh_token,
)

router = APIRouter(tags=["Auth"])


@router.post(
    "/auth/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(payload: RegisterRequest, request: Request):
    try:
        user = await register_user(payload.email, payload.password, payload.name)
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    return await issue_token_pair(user, request)


@router.post("/auth/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request):
    user = await authenticate_user(payload.email, payload.password)
    if user is None:
        raise _invalid_credentials()
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return await issue_token_pair(user, request)


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, request: Request):
    try:
        return await refresh_token_pair(payload.refresh_token, request)
    except InactiveUserError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    except InvalidRefreshTokenError:
        raise _invalid_refresh_token()


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: LogoutRequest):
    try:
        await revoke_refresh_token(payload.refresh_token)
    except InvalidRefreshTokenError:
        raise _invalid_refresh_token()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/auth/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(current_user: User = Depends(get_current_user)):
    await revoke_all_user_refresh_tokens(current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/auth/me", response_model=UserMeResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


def _invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
    )


def _invalid_refresh_token() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
    )
