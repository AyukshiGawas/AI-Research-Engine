"""Pydantic schemas for authentication requests and responses."""

from pydantic import BaseModel, Field
from app.schemas.user import UserRead


class LoginRequest(BaseModel):
    """Payload for user login requests."""

    username: str = Field(..., description="Email or Username")
    password: str = Field(..., description="Password")


class Token(BaseModel):
    """Token response schema returned upon successful authentication."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead


class MessageResponse(BaseModel):
    """Generic status message response schema."""

    message: str
