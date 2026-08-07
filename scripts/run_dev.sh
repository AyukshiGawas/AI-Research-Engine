#!/usr/bin/env bash
set -euo pipefail

if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

npm --prefix frontend run dev -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!

trap 'kill $BACKEND_PID $FRONTEND_PID' EXIT
wait
