"""Authentication service handling registration, login, refresh, and logout business logic."""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from fastapi import HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token_string,
    get_password_hash,
    hash_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.services.audit_service import AuditService


class AuthService:
    """Business logic for security authentication lifecycle."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_repo = TokenRepository(db)
        self.audit_service = AuditService(db)

    async def register(
        self,
        user_in: UserCreate,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> User:
        """Register a new user account."""
        # Check existing email
        if await self.user_repo.get_by_email(user_in.email):
            await self.audit_service.record_event(
                event_type="REGISTER_FAILED_DUPLICATE_EMAIL",
                ip_address=ip_address,
                user_agent=user_agent,
                details={"email": user_in.email},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is already registered.",
            )

        # Check existing username
        if await self.user_repo.get_by_username(user_in.username):
            await self.audit_service.record_event(
                event_type="REGISTER_FAILED_DUPLICATE_USERNAME",
                ip_address=ip_address,
                user_agent=user_agent,
                details={"username": user_in.username},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already taken.",
            )

        # Create user record
        user = User(
            email=user_in.email.lower(),
            username=user_in.username,
            full_name=user_in.full_name,
            hashed_password=get_password_hash(user_in.password),
        )
        created_user = await self.user_repo.create(user)

        await self.audit_service.record_event(
            event_type="REGISTER_SUCCESS",
            user_id=created_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return created_user

    async def login(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[User, str, str]:
        """Authenticate credentials and issue Access Token & Refresh Token pair."""
        user = await self.user_repo.get_by_identifier(username)
        if not user or not verify_password(password, user.hashed_password):
            await self.audit_service.record_event(
                event_type="LOGIN_FAILED",
                user_id=user.id if user else None,
                ip_address=ip_address,
                user_agent=user_agent,
                details={"reason": "invalid_credentials", "username": username},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username/email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            await self.audit_service.record_event(
                event_type="LOGIN_FAILED_INACTIVE",
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive.",
            )

        # Update last login timestamp
        await self.user_repo.update_last_login(user.id)

        # Generate Access Token (15 mins)
        access_token = create_access_token(data={"sub": str(user.id), "role": user.role})

        # Generate Refresh Token string & DB record (7 days)
        raw_refresh_token = create_refresh_token_string()
        token_hash = hash_token(raw_refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_record = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.token_repo.create(refresh_record)

        await self.audit_service.record_event(
            event_type="LOGIN_SUCCESS",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return user, access_token, raw_refresh_token

    async def refresh_tokens(
        self,
        raw_refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[User, str, str]:
        """Validate refresh token cookie, rotate token, and issue new credentials."""
        token_hash = hash_token(raw_refresh_token)
        token_record = await self.token_repo.get_by_hash(token_hash)

        if not token_record or token_record.is_revoked:
            await self.audit_service.record_event(
                event_type="TOKEN_REFRESH_FAILED_INVALID",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked refresh token.",
            )

        now = datetime.now(timezone.utc)
        if token_record.expires_at < now:
            await self.token_repo.revoke(token_record)
            await self.audit_service.record_event(
                event_type="TOKEN_REFRESH_FAILED_EXPIRED",
                user_id=token_record.user_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Expired refresh token.",
            )

        user = await self.user_repo.get_by_id(token_record.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account unavailable.",
            )

        # Token Rotation: Generate new Refresh Token
        new_raw_refresh_token = create_refresh_token_string()
        new_token_hash = hash_token(new_raw_refresh_token)
        new_expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        new_refresh_record = RefreshToken(
            user_id=user.id,
            token_hash=new_token_hash,
            expires_at=new_expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        created_new_record = await self.token_repo.create(new_refresh_record)

        # Revoke old refresh token and link replacement
        await self.token_repo.revoke(token_record, replaced_by_id=created_new_record.id)

        # Generate new Access Token
        new_access_token = create_access_token(data={"sub": str(user.id), "role": user.role})

        await self.audit_service.record_event(
            event_type="TOKEN_REFRESH_SUCCESS",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return user, new_access_token, new_raw_refresh_token

    async def logout(
        self,
        raw_refresh_token: Optional[str],
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """Revoke refresh token record in DB."""
        if raw_refresh_token:
            token_hash = hash_token(raw_refresh_token)
            token_record = await self.token_repo.get_by_hash(token_hash)
            if token_record:
                await self.token_repo.revoke(token_record)

        await self.audit_service.record_event(
            event_type="LOGOUT",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def set_refresh_cookie(self, response: Response, refresh_token_string: str) -> None:
        """Utility to attach HttpOnly refresh token cookie to HTTP response."""
        response.set_cookie(
            key="refresh_token",
            value=refresh_token_string,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            path="/api/v1/auth",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        )

    def clear_refresh_cookie(self, response: Response) -> None:
        """Utility to wipe HttpOnly refresh token cookie on response."""
        response.delete_cookie(
            key="refresh_token",
            path="/api/v1/auth",
        )
