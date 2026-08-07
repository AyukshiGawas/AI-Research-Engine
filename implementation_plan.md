# Phase 2 Implementation Plan: Authentication, PostgreSQL Integration & Dashboard Shell

This document details the architecture, database design, API specifications, frontend integration, testing strategy, sequence of execution, and rollback considerations for **Phase 2** of the **Enterprise AI Research Engine**.

---

## 1. Overview & Key Security Architectural Decisions

Phase 2 establishes enterprise identity, security, relational data persistence, and the post-login dashboard shell. 

### Key Architectural Upgrades:
- **HttpOnly Cookies for Refresh Tokens**: Refresh tokens are issued strictly as `HttpOnly`, `Secure`, `SameSite=Lax` cookies to prevent XSS-based token theft. Access tokens are short-lived (15 mins) and held in memory within the React Auth Context.
- **Token Revocation & `refresh_tokens` Table**: Every issued refresh token is hashed and tracked in PostgreSQL to support explicit logout, token rotation, and instant session revocation.
- **Consistent UUID Usage**: All database entities (`users`, `refresh_tokens`, `projects`, `audit_logs`) consistently use UUIDv4 primary keys and foreign key references.
- **Minimal `projects` Table**: Schema support for core enterprise workspace entities associated with users.
- **Audit Logging System**: Database and structured logging for all authentication events (`LOGIN_SUCCESS`, `LOGIN_FAILED`, `REGISTER_SUCCESS`, `TOKEN_REFRESH`, `LOGOUT`).
- **Strict Password Complexity**: Mandatory enforcement (min 12 chars, uppercase, lowercase, digit, special character).
- **Login Rate Limiting**: Protection against brute-force attacks limiting failed login attempts per IP address window.
- **Startup Configuration Validation**: Strict validation using `pydantic-settings` to block application initialization if required environment variables are missing or insecure.

---

## 2. Constraints & Import Conventions

> [!IMPORTANT]
> - **Backend Working Directory**: Backend execution command is always executed from the `backend/` working directory:
>   ```bash
>   uvicorn app.main:app --reload
>   ```
> - **Import Syntax Rule**: All Python module imports in the backend MUST strictly follow root-relative imports from `app`:
>   - **CORRECT**: `from app.core.config import settings`, `from app.db.session import get_db`, `from app.models.user import User`
>   - **FORBIDDEN**: `from backend.app...`

---

## 3. Directory & Folder Structure

```
AI-Research-Engine/
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── README
│   ├── alembic.ini
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── router.py
│   │   │       └── endpoints/
│   │   │           ├── health.py
│   │   │           ├── auth.py         # Register, Login, Refresh (Cookie), Logout, Revoke
│   │   │           ├── users.py        # User Profile (/me)
│   │   │           └── projects.py     # Minimal Project Workspace endpoints
│   │   ├── core/
│   │   │   ├── config.py               # Env Validation (pydantic-settings) & Startup checks
│   │   │   ├── logging.py
│   │   │   ├── security.py             # Password hashing (bcrypt) & JWT issuance/validation
│   │   │   └── rate_limit.py           # Slowapi / Redis rate limiter middleware
│   │   ├── db/
│   │   │   ├── base.py                 # Declarative Base & Model Registrations for Alembic
│   │   │   └── session.py              # SQLAlchemy Async/Sync Engine & SessionLocal
│   │   ├── dependencies/
│   │   │   ├── auth.py                 # get_current_user, get_current_active_user
│   │   │   └── rate_limit.py           # Rate limiting dependency injectors
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py                 # User SQLAlchemy model (UUID pk)
│   │   │   ├── refresh_token.py        # RefreshToken SQLAlchemy model (UUID pk)
│   │   │   ├── project.py              # Project SQLAlchemy model (UUID pk)
│   │   │   └── audit_log.py            # AuditLog SQLAlchemy model (UUID pk)
│   │   ├── repositories/
│   │   │   ├── user_repository.py
│   │   │   ├── token_repository.py
│   │   │   ├── project_repository.py
│   │   │   └── audit_repository.py
│   │   ├── schemas/
│   │   │   ├── auth.py                 # Token, Password Validation, Login schemas
│   │   │   ├── user.py                 # UserCreate, UserRead schemas
│   │   │   ├── project.py              # ProjectCreate, ProjectRead schemas
│   │   │   └── health.py
│   │   ├── services/
│   │   │   ├── auth_service.py         # Login logic, cookie issuance, token rotation
│   │   │   ├── audit_service.py        # Auth event audit logging
│   │   │   ├── project_service.py
│   │   │   └── user_service.py
│   │   └── main.py                     # Lifespan startup validation, middleware setup
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py                # Cookie auth, rate limiting & token revocation tests
│   │   ├── test_password_policy.py     # Password complexity validation tests
│   │   └── test_users.py
│   └── requirements.txt                # Updated with sqlalchemy, alembic, asyncpg, passlib, python-jose, slowapi
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   └── ProtectedRoute.jsx
│   │   ├── context/
│   │   │   └── AuthContext.jsx         # In-memory Access Token + Cookie-based silent refresh
│   │   ├── layouts/
│   │   │   └── DashboardLayout.jsx
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx
│   │   │   ├── RegisterPage.jsx
│   │   │   ├── DashboardPage.jsx
│   │   │   └── ProfilePage.jsx
│   │   ├── services/
│   │   │   ├── api.js                  # Axios client with withCredentials: true & auto-refresh
│   │   │   └── authService.js
│   │   ├── App.jsx
│   │   └── index.css
│   └── package.json
└── docker-compose.yml                  # PostgreSQL service
```

---

## 4. Database Schema (PostgreSQL & SQLAlchemy ORM with UUIDs)

All tables use `UUID` (UUIDv4) primary keys generated by `gen_random_uuid()`.

### 4.1 Table: `users`
| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default: `gen_random_uuid()` | Unique user ID |
| `email` | `VARCHAR(255)` | Unique, Indexed, NOT NULL | Primary email |
| `username` | `VARCHAR(100)` | Unique, Indexed, NOT NULL | Username |
| `full_name` | `VARCHAR(255)` | Nullable | User full name |
| `hashed_password` | `VARCHAR(255)` | NOT NULL | Bcrypt hashed password |
| `role` | `VARCHAR(50)` | Default: `'researcher'`, NOT NULL | Role (`admin`, `researcher`, `viewer`) |
| `is_active` | `BOOLEAN` | Default: `TRUE`, NOT NULL | Active status |
| `is_superuser` | `BOOLEAN` | Default: `FALSE`, NOT NULL | Superuser flag |
| `last_login_at` | `TIMESTAMP WITH TIME ZONE` | Nullable | Last login timestamp |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Default: `NOW()`, NOT NULL | Creation timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | Default: `NOW()`, NOT NULL | Last update timestamp |

### 4.2 Table: `refresh_tokens`
| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default: `gen_random_uuid()` | Refresh token record ID |
| `user_id` | `UUID` | Foreign Key -> `users.id` (ON DELETE CASCADE), Indexed, NOT NULL | Associated user ID |
| `token_hash` | `VARCHAR(255)` | Unique, Indexed, NOT NULL | SHA-256 hash of refresh token |
| `expires_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | Token expiration date |
| `is_revoked` | `BOOLEAN` | Default: `FALSE`, NOT NULL | Revocation status |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Default: `NOW()`, NOT NULL | Creation timestamp |
| `replaced_by_id` | `UUID` | Nullable Foreign Key -> `refresh_tokens.id` | Token rotation link |
| `user_agent` | `VARCHAR(512)` | Nullable | User agent header |
| `ip_address` | `VARCHAR(45)` | Nullable | Client IP address |

### 4.3 Table: `projects` (Minimal Phase 2 Workspace Support)
| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default: `gen_random_uuid()` | Project ID |
| `owner_id` | `UUID` | Foreign Key -> `users.id` (ON DELETE CASCADE), Indexed, NOT NULL | Project owner ID |
| `name` | `VARCHAR(255)` | NOT NULL | Project name |
| `description` | `TEXT` | Nullable | Description |
| `status` | `VARCHAR(50)` | Default: `'active'`, NOT NULL | Status (`active`, `archived`) |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Default: `NOW()`, NOT NULL | Creation timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | Default: `NOW()`, NOT NULL | Last update timestamp |

### 4.4 Table: `audit_logs`
| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default: `gen_random_uuid()` | Audit entry ID |
| `user_id` | `UUID` | Nullable Foreign Key -> `users.id` (ON DELETE SET NULL), Indexed | Associated user ID |
| `event_type` | `VARCHAR(100)` | Indexed, NOT NULL | Event code (`LOGIN_SUCCESS`, `LOGIN_FAILED`, `REGISTER_SUCCESS`, `TOKEN_REFRESH`, `LOGOUT`) |
| `ip_address` | `VARCHAR(45)` | Nullable | Client IP address |
| `user_agent` | `VARCHAR(512)` | Nullable | Client User Agent |
| `details` | `JSONB` | Nullable | Event metadata (e.g. failure reason, attempt count) |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Default: `NOW()`, NOT NULL | Log timestamp |

---

## 5. Security & Business Rules Specification

### 5.1 Password Complexity Requirements
Registration (`UserCreate`) and password updates strictly enforce the following rules via Pydantic validator:
- Minimum length: **12 characters**.
- Must contain at least **one uppercase letter** (`A-Z`).
- Must contain at least **one lowercase letter** (`a-z`).
- Must contain at least **one digit** (`0-9`).
- Must contain at least **one special character** (`!@#$%^&*()_+-=[]{}|;:,.<>?`).

### 5.2 Login Rate Limiting
- Configured via `slowapi` middleware in `backend/app/core/rate_limit.py`.
- `/api/v1/auth/login` endpoint is rate limited to **5 attempts per minute per IP address**.
- Exceeding attempts returns `HTTP 429 Too Many Requests` and records an audit log entry (`LOGIN_RATE_LIMITED`).

### 5.3 Startup Environment Variable Validation
On application startup (lifespan hook in `app/main.py`), `app/core/config.py` validates:
- `DATABASE_URL` / PostgreSQL credentials are provided and non-empty.
- `SECRET_KEY` is present and at least 32 characters long; fails startup if set to default values like `"secret"` or `"change_me"`.
- `JWT_ALGORITHM` (e.g., `HS256`).
- `ACCESS_TOKEN_EXPIRE_MINUTES` (e.g., 15) and `REFRESH_TOKEN_EXPIRE_DAYS` (e.g., 7).
- If validation fails, application prints structured error logs and halts initialization.

---

## 6. API Endpoints Specification

### 6.1 Authentication Endpoints

#### `POST /api/v1/auth/register`
- **Access**: Public (Rate limited: 5 requests / min / IP)
- **Request Body**:
  ```json
  {
    "email": "user@enterprise.com",
    "username": "johndoe",
    "password": "SecurePassword123!",
    "full_name": "John Doe"
  }
  ```
- **Responses**:
  - `201 Created`: User created. Audit event `REGISTER_SUCCESS` logged. Returns `UserRead` schema.
  - `400 Bad Request`: Email/Username already taken.
  - `422 Unprocessable Entity`: Password policy violation (fails complexity check).

#### `POST /api/v1/auth/login`
- **Access**: Public (Rate limited: 5 requests / min / IP)
- **Request Body**:
  ```json
  {
    "username": "user@enterprise.com",
    "password": "SecurePassword123!"
  }
  ```
- **Responses**:
  - `200 OK`: Sets `HttpOnly` cookie for refresh token and returns access token in body:
    - **Header**: `Set-Cookie: refresh_token=<uuid_token>; HttpOnly; Secure; SameSite=Lax; Path=/api/v1/auth; Max-Age=604800`
    - **Body**:
      ```json
      {
        "access_token": "eyJhbGciOiJIUzI1Ni...",
        "token_type": "bearer",
        "expires_in": 900,
        "user": {
          "id": "c1f2e3d4-...",
          "email": "user@enterprise.com",
          "username": "johndoe",
          "role": "researcher"
        }
      }
      ```
    - Audit event `LOGIN_SUCCESS` logged.
  - `401 Unauthorized`: Incorrect credentials. Audit event `LOGIN_FAILED` logged.
  - `429 Too Many Requests`: Rate limit exceeded.

#### `POST /api/v1/auth/refresh`
- **Access**: Cookie-based (`refresh_token` HttpOnly cookie)
- **Responses**:
  - `200 OK`: Validates cookie token hash against `refresh_tokens` table. Performs token rotation (revokes old token, issues new refresh token cookie, returns new 15-min Access Token). Audit event `TOKEN_REFRESH` logged.
  - `401 Unauthorized`: Cookie missing, token expired, or token revoked. Clears cookie (`Max-Age=0`).

#### `POST /api/v1/auth/logout`
- **Access**: Protected / Cookie-based
- **Responses**:
  - `200 OK`: Revokes current refresh token record (`is_revoked = true`) in `refresh_tokens` table. Clears `refresh_token` cookie. Audit event `LOGOUT` logged.

---

### 6.2 User & Project Endpoints

#### `GET /api/v1/users/me`
- **Access**: Protected (Bearer Access Token required)
- **Headers**: `Authorization: Bearer <access_token>`
- **Responses**: `200 OK` (User details), `401 Unauthorized`.

#### `GET /api/v1/projects` & `POST /api/v1/projects`
- **Access**: Protected (Bearer Access Token required)
- **Description**: Minimal project management endpoints to power the Dashboard Shell workspace list.

---

## 7. Frontend Architecture & Flow

### 7.1 Frontend Axios Setup (`services/api.js`)
- Configured with `withCredentials: true` so HttpOnly cookies are automatically sent with refresh & logout requests.
- Axios request interceptor attaches `Authorization: Bearer <in_memory_access_token>`.
- Axios response interceptor catches `401` errors on protected requests and automatically attempts a single token refresh call (`POST /api/v1/auth/refresh`), retrying the failed request upon success.

---

## 8. Sequence of Implementation

### Step 1: Dependencies, Environment Validation & Rate Limiting
- Add `slowapi` to `backend/requirements.txt`.
- Update `backend/app/core/config.py` with `pydantic-settings` validation rules and startup sanity checks.
- Implement rate limiting middleware in `backend/app/core/rate_limit.py`.

### Step 2: Database Schema & Alembic Migration
- Implement SQLAlchemy UUID models in `app/models/`:
  - `user.py` (`users` table)
  - `refresh_token.py` (`refresh_tokens` table)
  - `project.py` (`projects` table)
  - `audit_log.py` (`audit_logs` table)
- Configure `alembic/env.py` and run migration: `alembic revision --autogenerate -m "create Phase 2 tables with UUIDs"` and `alembic upgrade head`.

### Step 3: Security & Audit Infrastructure
- Implement password complexity regex validator in `app/schemas/user.py`.
- Implement audit service in `app/services/audit_service.py` to record events into `audit_logs`.
- Implement refresh token generator, SHA-256 hashing, and cookie response setters in `app/core/security.py`.

### Step 4: Auth Service & Endpoints
- Implement `POST /api/v1/auth/register`, `POST /api/v1/auth/login` (sets HttpOnly cookie), `POST /api/v1/auth/refresh`, and `POST /api/v1/auth/logout`.
- Implement `GET /api/v1/users/me` and `GET /api/v1/projects`.

### Step 5: Frontend Auth Context & Interceptors
- Update `frontend/src/services/api.js` with `withCredentials: true` and `401` auto-refresh response interceptor.
- Update `frontend/src/context/AuthContext.jsx` to store access tokens in memory and perform initial silent refresh on app load.

### Step 6: Frontend Views & Dashboard Shell
- Update `LoginPage.jsx` and `RegisterPage.jsx` displaying field validation errors.
- Implement `DashboardLayout.jsx` displaying minimal projects list, user badge, and logout control.

---

## 9. Verification & Testing Strategy

### 9.1 Backend Automated Testing (`pytest`)
- **Password Policy (`tests/test_password_policy.py`)**: Test weak passwords (missing digit, short length) fail schema validation.
- **Cookie Auth & Refresh (`tests/test_auth.py`)**:
  - Test `/login` returns access token in body and `refresh_token` in `Set-Cookie` header.
  - Test `/refresh` works with valid cookie and rotates refresh token in DB.
  - Test revoked refresh tokens cannot be reused.
- **Rate Limiting (`tests/test_auth.py`)**: Test >5 rapid failed login attempts return `HTTP 429`.
- **Audit Logs (`tests/test_auth.py`)**: Verify audit log records are created in DB after login/register events.

### 9.2 Manual Verification
1. Verify browser Developer Tools -> Application -> Cookies: `refresh_token` is present, `HttpOnly` is checked, and token is not accessible via JavaScript (`document.cookie`).
2. Verify Local Storage is empty of secret refresh tokens.
3. Test brute force login: trigger 6 failed attempts and verify `429 Too Many Requests`.
4. Check PostgreSQL database `audit_logs` table to confirm entries for all actions.

---

## 10. Rollback Considerations

- Database migrations can be safely rolled back using `alembic downgrade -1`.
- API backward compatibility is preserved for health endpoints (`/api/v1/health`), ensuring container orchestrator probes are unaffected by auth/database changes.
