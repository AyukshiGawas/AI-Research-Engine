# Enterprise AI Research Engine

An enterprise-grade AI Research Engine for managing, processing, and analyzing research documents. The project is built with a modern FastAPI backend and a React frontend using a clean architecture that prepares the system for AI-powered document processing, semantic search, and multi-agent research workflows.

---

## Current Status

**Current Version:** v0.3.0

### Completed Phases

- ✅ Phase 1 – Project Foundation
- ✅ Phase 2 – Authentication & Project Management
- ✅ Phase 3 – Research Workspace & Document Management

---

# Features

## Backend

- FastAPI
- SQLAlchemy ORM
- Alembic Migrations
- PostgreSQL-ready Architecture
- Repository Pattern
- Service Layer
- Dependency Injection
- JWT Authentication
- Refresh Tokens
- Audit Logging
- User Management
- Project Management
- Secure Document Upload
- Local File Storage
- Document Metadata Management
- Document Download
- Document Deletion
- File Validation
- UUID-based Entities

---

## Frontend

- React 18
- React Router
- Context API
- Protected Routes
- Dashboard
- Project Management
- Document Workspace
- Document Upload
- Document Listing
- Download Documents
- Delete Documents
- Responsive UI

---

# Supported Documents

| Type | Supported |
|------|-----------|
| PDF | ✅ |
| DOCX | ✅ |
| TXT | ✅ |
| Markdown | ✅ |

Maximum upload size:

```
25 MB
```

---

# Technology Stack

## Backend

- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL (Primary)
- SQLite (Development)
- JWT Authentication

## Frontend

- React
- Vite
- React Router
- Context API

## DevOps

- Docker
- Docker Compose
- GitHub Actions

---

# Project Structure

```text
AI-Research-Engine/

backend/
│
├── alembic/
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── dependencies/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   ├── validators/
│   └── main.py
│
├── uploads/
└── tests/

frontend/
│
├── src/
│   ├── components/
│   ├── hooks/
│   ├── pages/
│   ├── services/
│   ├── utils/
│   └── tests/
│
└── public/
```

---

# Running the Project

## Backend

```bash
cd backend

python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Backend:

```
http://127.0.0.1:8000
```

---

## Frontend

```bash
cd frontend

npm install

npm run dev
```

Frontend:

```
http://localhost:5173
```

---

# Running Tests

## Backend

```bash
cd backend

python -m pytest
```

Current Status

```
16 Backend Tests Passed
```

---

## Frontend

```bash
cd frontend

npx vitest run
```

Current Status

```
4 Test Files
7 Tests Passed
```

---

# Completed Roadmap

- ✅ Phase 1 – Foundation
- ✅ Phase 2 – Authentication
- ✅ Phase 3 – Document Management

---

# Upcoming Roadmap

- ⏳ Phase 4 – Document Processing
- ⏳ Phase 5 – Chunking Pipeline
- ⏳ Phase 6 – Embeddings
- ⏳ Phase 7 – Semantic Search
- ⏳ Phase 8 – Multi-Agent Research Engine

---

# Architecture

The project follows enterprise software engineering principles.

- Clean Architecture
- Repository Pattern
- Service Layer
- Dependency Injection
- REST API
- UUID-based Models
- Environment-based Configuration
- Docker-first Development

Business logic is isolated from API routes, ensuring scalability and maintainability.

---

# License

This project is intended for educational and research purposes.