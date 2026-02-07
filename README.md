# Game Instant Matching

大人が無料で、スキマ時間に、1戦だけ気軽に遊べるゲームマッチングWebアプリ。

## Quick Start

```bash
# 1. Start PostgreSQL
docker compose up -d

# 2. Backend
cd apps/api
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000

# 3. Frontend
cd apps/web
pnpm install
pnpm dev

# 4. Open http://localhost:5173
```

## Flow

1. ニックネーム入力でログイン
2. ロビーで募集一覧を確認 / 新規募集を作成
3. 別ユーザーが参加 → マッチ成立 → ルーム作成
4. ルーム内チャットで集合調整
5. 1戦終了後にルームクローズ → フィードバック（👍/👎）

## Tech Stack

- **Frontend**: Vue 3 + Vite + TypeScript + Tailwind CSS + Pinia
- **Backend**: FastAPI + SQLAlchemy (async) + Alembic + Pydantic v2
- **Database**: PostgreSQL 17

## Development Commands

```bash
# Backend
cd apps/api
uv run pytest -q          # テスト
uv run ruff check .       # Lint
uv run ruff format .      # Format

# Frontend
cd apps/web
pnpm dev                  # Dev server
pnpm build                # Build
pnpm lint                 # Lint
pnpm test                 # Test
```
