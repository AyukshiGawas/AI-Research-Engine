# AI Research Engine

A Phase 1 scaffold for an enterprise-style AI research platform with a FastAPI backend, a React + Vite frontend, Docker-based support, and placeholder architecture for future integrations.

## Features
- FastAPI backend with health and version endpoints
- React + Vite frontend shell
- Docker Compose with placeholder services
- Basic CI workflow
- Placeholder folders for future backend and frontend expansion

## Start locally

### Backend
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
npm --prefix frontend install
npm --prefix frontend run dev -- --host 0.0.0.0 --port 5173
```

### PowerShell
```powershell
./scripts/run_dev.ps1
```

## Verification
- Visit http://127.0.0.1:8000/health
- Visit http://127.0.0.1:8000/api/v1/version
- Visit http://127.0.0.1:5173