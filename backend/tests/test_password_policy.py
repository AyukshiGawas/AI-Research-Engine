"""Unit tests for password complexity policy validation."""

import pytest
from pydantic import ValidationError
from app.schemas.user import UserCreate


def test_valid_password_complexity():
    """Test valid password passing complexity rules."""
    user = UserCreate(
        email="test@enterprise.com",
        username="validuser",
        password="SecurePassword123!",
        full_name="Valid User",
    )
    assert user.password == "SecurePassword123!"


def test_password_too_short():
    """Test password under 12 characters fails validation."""
    with pytest.raises(ValidationError) as exc:
        UserCreate(
            email="test@enterprise.com",
            username="shortuser",
            password="Short1!",
        )
    assert "Password must be at least 12 characters long" in str(exc.value)


def test_password_missing_uppercase():
    """Test password lacking uppercase character fails validation."""
    with pytest.raises(ValidationError) as exc:
        UserCreate(
            email="test@enterprise.com",
            username="nouppercase",
            password="securepassword123!",
        )
    assert "at least one uppercase letter" in str(exc.value)


def test_password_missing_digit():
    """Test password lacking digit fails validation."""
    with pytest.raises(ValidationError) as exc:
        UserCreate(
            email="test@enterprise.com",
            username="nodigit",
            password="SecurePassword!",
        )
    assert "at least one digit" in str(exc.value)


def test_password_missing_special_character():
    """Test password lacking special character fails validation."""
    with pytest.raises(ValidationError) as exc:
        UserCreate(
            email="test@enterprise.com",
            username="nospecial",
            password="SecurePassword123",
        )
    assert "at least one special character" in str(exc.value)
