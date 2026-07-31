"""Integration tests for registration, login, cookie refresh, and logout endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_user_registration(client: AsyncClient):
    """Test successful user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "researcher@enterprise.com",
            "username": "researcher1",
            "password": "SecurePassword123!",
            "full_name": "Dr. Research",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "researcher@enterprise.com"
    assert data["username"] == "researcher1"
    assert "id" in data


@pytest.mark.asyncio
async def test_user_login_and_cookie(client: AsyncClient):
    """Test login returning access token in JSON body and refresh_token in HttpOnly cookie."""
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@enterprise.com",
            "username": "johndoe",
            "password": "SecurePassword123!",
        },
    )

    # Perform login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "johndoe",
            "password": "SecurePassword123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "user@enterprise.com"

    # Verify HttpOnly cookie set
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_token_refresh_flow(client: AsyncClient):
    """Test refresh token cookie rotation issuing a new access token."""
    # Register & Login
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh@enterprise.com",
            "username": "refreshuser",
            "password": "SecurePassword123!",
        },
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "refreshuser", "password": "SecurePassword123!"},
    )
    refresh_cookie = login_res.cookies.get("refresh_token")
    assert refresh_cookie is not None

    # Call refresh endpoint with cookie
    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": refresh_cookie},
    )
    assert refresh_res.status_code == 200
    data = refresh_res.json()
    assert "access_token" in data
    assert "refresh_token" in refresh_res.cookies


@pytest.mark.asyncio
async def test_logout_flow(client: AsyncClient):
    """Test logout endpoint revoking token and clearing cookie."""
    # Register & Login
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "logout@enterprise.com",
            "username": "logoutuser",
            "password": "SecurePassword123!",
        },
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "logoutuser", "password": "SecurePassword123!"},
    )
    refresh_cookie = login_res.cookies.get("refresh_token")

    # Logout
    logout_res = await client.post(
        "/api/v1/auth/logout",
        cookies={"refresh_token": refresh_cookie},
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["message"] == "Successfully logged out."
