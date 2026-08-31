"""Pydantic schemas for User entity validation and responses."""

import re
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Registration schema with password complexity validation."""

    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    password: str = Field(..., description="Plain-text password")
    full_name: Optional[str] = Field(None, max_length=255, description="User full name")

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, value: str) -> str:
        """Validate password complexity rules.

        Rules:
        - At least 12 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if len(value) < 12:
            raise ValueError("Password must be at least 12 characters long.")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", value):
            raise ValueError("Password must contain at least one special character.")
        return value


class UserRead(BaseModel):
    """Schema for public user profile data."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None


class UserUpdate(BaseModel):
    """Schema for user profile update requests."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_optional_password(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            return UserCreate.validate_password_complexity(value)
        return value


VALID_ROLES = {"admin", "researcher", "analyst"}


class UserStatusUpdate(BaseModel):
    """Schema for updating a user's active/inactive status."""

    is_active: bool = Field(..., description="Whether the user account is active")


class UserRoleUpdate(BaseModel):
    """Schema for updating a user's authorization role."""

    role: str = Field(..., description="Assigned user role ('admin', 'researcher', 'analyst')")

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        role_clean = value.strip().lower()
        if role_clean not in VALID_ROLES:
            raise ValueError(
                f"Invalid role '{value}'. Supported roles: {', '.join(sorted(VALID_ROLES))}"
            )
        return role_clean
