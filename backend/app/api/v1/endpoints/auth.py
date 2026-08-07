"""Authentication API endpoints."""

from typing import Optional
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.dependencies.auth import get_current_user, get_current_user_optional
from app.models.user import User
from app.schemas.auth import LoginRequest, MessageResponse, Token
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """Register a new user account."""
    auth_service = AuthService(db)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    user = await auth_service.register(
        user_in=user_in,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    return user


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Authenticate credentials, set HttpOnly refresh token cookie, and return access token."""
    auth_service = AuthService(db)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    user, access_token, raw_refresh_token = await auth_service.login(
        username=login_data.username,
        password=login_data.password,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    # Attach HttpOnly cookie
    auth_service.set_refresh_cookie(response, raw_refresh_token)

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user,
    )


@router.post("/refresh", response_model=Token)
async def refresh(
    request: Request,
    response: Response,
    refresh_token: Optional[str] = Cookie(None, alias="refresh_token"),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Rotate refresh token using HttpOnly cookie and return a new access token."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token cookie missing.",
        )

    auth_service = AuthService(db)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    user, new_access_token, new_raw_refresh_token = await auth_service.refresh_tokens(
        raw_refresh_token=refresh_token,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    # Attach updated HttpOnly cookie
    auth_service.set_refresh_cookie(response, new_raw_refresh_token)

    return Token(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response,
    refresh_token: Optional[str] = Cookie(None, alias="refresh_token"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Revoke refresh token and wipe HttpOnly cookie."""
    auth_service = AuthService(db)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    user_id = current_user.id if current_user else None

    await auth_service.logout(
        raw_refresh_token=refresh_token,
        user_id=user_id,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    auth_service.clear_refresh_cookie(response)
    return MessageResponse(message="Successfully logged out.")
