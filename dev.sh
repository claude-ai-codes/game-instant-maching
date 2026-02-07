#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PATH="$HOME/.npm-global/bin:$PATH"

cleanup() {
  echo ""
  echo "Shutting down..."
  kill $PID_API $PID_WEB 2>/dev/null || true
  wait $PID_API $PID_WEB 2>/dev/null || true
  echo "Done."
}
trap cleanup EXIT INT TERM

# Backend (FastAPI)
echo "Starting backend on http://127.0.0.1:8000 ..."
cd "$ROOT_DIR/apps/api"
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 &
PID_API=$!

# Frontend (Vite)
echo "Starting frontend on http://localhost:5173 ..."
cd "$ROOT_DIR/apps/web"
pnpm dev &
PID_WEB=$!

echo "Press Ctrl+C to stop both servers."
wait
