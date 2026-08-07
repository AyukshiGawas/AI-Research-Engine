"""Integration tests for protected user profile endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_user_me_unauthorized(client: AsyncClient):
    """Test accessing /api/v1/users/me without token fails with 401."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_user_me_authorized(client: AsyncClient):
    """Test accessing /api/v1/users/me with valid Bearer token returns profile data."""
    # Register & Login
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "me@enterprise.com",
            "username": "meuser",
            "password": "SecurePassword123!",
            "full_name": "Me User",
        },
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "meuser", "password": "SecurePassword123!"},
    )
    token = login_res.json()["access_token"]

    # Request /me
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@enterprise.com"
    assert data["username"] == "meuser"
    assert data["full_name"] == "Me User"
