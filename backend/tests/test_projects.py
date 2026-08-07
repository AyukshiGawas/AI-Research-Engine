"""Integration tests for minimal project endpoints (GET and POST)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_project_create_and_list(client: AsyncClient):
    """Test minimal project creation (POST) and list (GET) for authenticated user."""
    # Register & Login
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "proj@enterprise.com",
            "username": "projuser",
            "password": "SecurePassword123!",
        },
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "projuser", "password": "SecurePassword123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. List projects initially (should be empty)
    list_res = await client.get("/api/v1/projects/", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json() == []

    # 2. Create project (POST)
    create_res = await client.post(
        "/api/v1/projects/",
        headers=headers,
        json={
            "name": "Quantum NLP AI Engine",
            "description": "Enterprise multi-agent quantum NLP research workspace.",
        },
    )
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["name"] == "Quantum NLP AI Engine"
    assert "id" in created_data

    # 3. List projects (GET) -> should contain newly created project
    list_res2 = await client.get("/api/v1/projects/", headers=headers)
    assert list_res2.status_code == 200
    projects = list_res2.json()
    assert len(projects) == 1
    assert projects[0]["name"] == "Quantum NLP AI Engine"
