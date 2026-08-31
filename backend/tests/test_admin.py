"""Integration tests for Phase 10: Enterprise RBAC & Admin User Management."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.audit_log import AuditLog
from app.models.user import User


# ---------------------------------------------------------------------------
# Helper functions for creating test users
# ---------------------------------------------------------------------------


async def _create_test_user(
    db: AsyncSession,
    email: str,
    username: str,
    role: str = "researcher",
    is_active: bool = True,
    is_superuser: bool = False,
) -> User:
    """Create and persist a user in the test database."""
    user = User(
        email=email,
        username=username,
        hashed_password="hashed_secure_password",
        full_name=f"Test {username.capitalize()}",
        role=role,
        is_active=is_active,
        is_superuser=is_superuser,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


def _auth_headers(user: User) -> dict:
    """Generate Authorization header with valid JWT token."""
    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Authorization & RBAC Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_admin_endpoints_require_authentication(client: AsyncClient):
    """Accessing any admin endpoint without authentication returns 401."""
    random_uuid = uuid.uuid4()
    assert (await client.get("/api/v1/admin/users")).status_code == 401
    assert (await client.get(f"/api/v1/admin/users/{random_uuid}")).status_code == 401
    assert (await client.patch(f"/api/v1/admin/users/{random_uuid}/status", json={"is_active": False})).status_code == 401
    assert (await client.patch(f"/api/v1/admin/users/{random_uuid}/role", json={"role": "admin"})).status_code == 401


@pytest.mark.asyncio
async def test_researcher_forbidden_from_admin_endpoints(client: AsyncClient, db_session: AsyncSession):
    """Authenticated researcher (non-admin) receives 403 Forbidden on all admin endpoints."""
    researcher = await _create_test_user(db_session, "res1@enterprise.com", "researcher1", role="researcher")
    headers = _auth_headers(researcher)
    random_uuid = uuid.uuid4()

    res_list = await client.get("/api/v1/admin/users", headers=headers)
    assert res_list.status_code == 403
    assert "Admin privileges required" in res_list.json()["detail"]

    res_get = await client.get(f"/api/v1/admin/users/{random_uuid}", headers=headers)
    assert res_get.status_code == 403

    res_status = await client.patch(f"/api/v1/admin/users/{random_uuid}/status", json={"is_active": False}, headers=headers)
    assert res_status.status_code == 403

    res_role = await client.patch(f"/api/v1/admin/users/{random_uuid}/role", json={"role": "admin"}, headers=headers)
    assert res_role.status_code == 403


@pytest.mark.asyncio
async def test_inactive_admin_forbidden(client: AsyncClient, db_session: AsyncSession):
    """An inactive admin user receives 403 Forbidden."""
    inactive_admin = await _create_test_user(db_session, "inactive_admin@enterprise.com", "inactadmin", role="admin", is_active=False)
    headers = _auth_headers(inactive_admin)

    res = await client.get("/api/v1/admin/users", headers=headers)
    assert res.status_code == 403
    assert "Inactive user account" in res.json()["detail"]


# ---------------------------------------------------------------------------
# Admin User Management Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_admin_list_users(client: AsyncClient, db_session: AsyncSession):
    """Admin can list all registered users."""
    admin = await _create_test_user(db_session, "admin_list@enterprise.com", "admin_list", role="admin")
    u1 = await _create_test_user(db_session, "u1@enterprise.com", "u1_list", role="researcher")
    u2 = await _create_test_user(db_session, "u2@enterprise.com", "u2_list", role="analyst")

    headers = _auth_headers(admin)
    response = await client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    user_emails = [u["email"] for u in data]
    assert admin.email in user_emails
    assert u1.email in user_emails
    assert u2.email in user_emails

    # Verify sensitive data is NOT exposed
    for u in data:
        assert "hashed_password" not in u
        assert "password" not in u


@pytest.mark.asyncio
async def test_admin_get_user_by_id(client: AsyncClient, db_session: AsyncSession):
    """Admin can retrieve a specific user profile by ID."""
    admin = await _create_test_user(db_session, "admin_get@enterprise.com", "admin_get", role="admin")
    target = await _create_test_user(db_session, "target@enterprise.com", "target_user", role="researcher")

    headers = _auth_headers(admin)
    response = await client.get(f"/api/v1/admin/users/{target.id}", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == str(target.id)
    assert data["email"] == "target@enterprise.com"
    assert data["username"] == "target_user"
    assert data["role"] == "researcher"
    assert data["is_active"] is True
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_admin_get_user_nonexistent_returns_404(client: AsyncClient, db_session: AsyncSession):
    """Requesting nonexistent user returns 404."""
    admin = await _create_test_user(db_session, "admin_404@enterprise.com", "admin_404", role="admin")
    headers = _auth_headers(admin)

    fake_id = uuid.uuid4()
    response = await client.get(f"/api/v1/admin/users/{fake_id}", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_admin_update_user_status(client: AsyncClient, db_session: AsyncSession):
    """Admin can deactivate and activate a user account with audit trail."""
    admin = await _create_test_user(db_session, "admin_status@enterprise.com", "admin_status", role="admin")
    target = await _create_test_user(db_session, "target_status@enterprise.com", "target_status", role="researcher", is_active=True)

    headers = _auth_headers(admin)

    # 1. Deactivate user
    res_deact = await client.patch(
        f"/api/v1/admin/users/{target.id}/status",
        json={"is_active": False},
        headers=headers,
    )
    assert res_deact.status_code == 200
    assert res_deact.json()["is_active"] is False

    # Verify DB persistence
    await db_session.refresh(target)
    assert target.is_active is False

    # 2. Reactivate user
    res_act = await client.patch(
        f"/api/v1/admin/users/{target.id}/status",
        json={"is_active": True},
        headers=headers,
    )
    assert res_act.status_code == 200
    assert res_act.json()["is_active"] is True

    await db_session.refresh(target)
    assert target.is_active is True

    # 3. Check audit log entries
    stmt = select(AuditLog).where(
        AuditLog.event_type == "ADMIN_USER_STATUS_UPDATED",
        AuditLog.user_id == admin.id,
    )
    logs = (await db_session.execute(stmt)).scalars().all()
    assert len(logs) == 2
    assert logs[0].details["target_user_id"] == str(target.id)
    assert logs[0].details["previous_status"] is True
    assert logs[0].details["new_status"] is False


@pytest.mark.asyncio
async def test_admin_update_user_role(client: AsyncClient, db_session: AsyncSession):
    """Admin can promote or change a user's role with audit trail."""
    admin = await _create_test_user(db_session, "admin_role@enterprise.com", "admin_role", role="admin")
    target = await _create_test_user(db_session, "target_role@enterprise.com", "target_role", role="researcher")

    headers = _auth_headers(admin)

    # 1. Change role: researcher -> analyst
    res_analyst = await client.patch(
        f"/api/v1/admin/users/{target.id}/role",
        json={"role": "analyst"},
        headers=headers,
    )
    assert res_analyst.status_code == 200
    assert res_analyst.json()["role"] == "analyst"

    await db_session.refresh(target)
    assert target.role == "analyst"

    # 2. Change role: analyst -> admin
    res_admin = await client.patch(
        f"/api/v1/admin/users/{target.id}/role",
        json={"role": "admin"},
        headers=headers,
    )
    assert res_admin.status_code == 200
    assert res_admin.json()["role"] == "admin"

    await db_session.refresh(target)
    assert target.role == "admin"

    # 3. Check audit log entries
    stmt = select(AuditLog).where(
        AuditLog.event_type == "ADMIN_USER_ROLE_UPDATED",
        AuditLog.user_id == admin.id,
    )
    logs = (await db_session.execute(stmt)).scalars().all()
    assert len(logs) == 2
    assert logs[0].details["previous_role"] == "researcher"
    assert logs[0].details["new_role"] == "analyst"
    assert logs[1].details["previous_role"] == "analyst"
    assert logs[1].details["new_role"] == "admin"


@pytest.mark.asyncio
async def test_admin_update_role_invalid_role_fails(client: AsyncClient, db_session: AsyncSession):
    """Supplying an unsupported role string returns 422 validation error."""
    admin = await _create_test_user(db_session, "admin_invalid_role@enterprise.com", "admin_inv_role", role="admin")
    target = await _create_test_user(db_session, "target_inv@enterprise.com", "target_inv", role="researcher")

    headers = _auth_headers(admin)
    response = await client.patch(
        f"/api/v1/admin/users/{target.id}/role",
        json={"role": "super_hacker"},
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_admin_update_nonexistent_user_returns_404(client: AsyncClient, db_session: AsyncSession):
    """Patching status or role for nonexistent user ID returns 404."""
    admin = await _create_test_user(db_session, "admin_no_user@enterprise.com", "admin_no_user", role="admin")
    headers = _auth_headers(admin)
    fake_id = uuid.uuid4()

    res_status = await client.patch(f"/api/v1/admin/users/{fake_id}/status", json={"is_active": False}, headers=headers)
    assert res_status.status_code == 404

    res_role = await client.patch(f"/api/v1/admin/users/{fake_id}/role", json={"role": "analyst"}, headers=headers)
    assert res_role.status_code == 404


# ---------------------------------------------------------------------------
# Self-Service /users/me Compatibility Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_users_me_behavior_remains_unchanged(client: AsyncClient, db_session: AsyncSession):
    """Existing self-service GET and PUT /api/v1/users/me endpoints continue to work for researchers."""
    researcher = await _create_test_user(db_session, "self_res@enterprise.com", "self_res", role="researcher")
    headers = _auth_headers(researcher)

    # 1. GET /me
    res_get = await client.get("/api/v1/users/me", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["email"] == "self_res@enterprise.com"
    assert res_get.json()["role"] == "researcher"

    # 2. PUT /me
    res_put = await client.put(
        "/api/v1/users/me",
        json={"full_name": "Updated Self Researcher"},
        headers=headers,
    )
    assert res_put.status_code == 200
    assert res_put.json()["full_name"] == "Updated Self Researcher"
