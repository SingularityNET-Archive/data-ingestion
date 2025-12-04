# Quickstart — Ingestion Dashboard (Prototype)

Prerequisites

- Python 3.11
- Node.js 18+ and npm/yarn
- Access to the project's `DATABASE_URL` (Supabase/Postgres)

Backend (FastAPI) — quick run

1. Create a virtual env and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn asyncpg pydantic
```

2. Set environment variables (for local dev):

```bash
export DATABASE_URL="${DATABASE_URL}"
export ENV=development
```

3. Run the backend (example):

```bash
uvicorn backend.app.main:app --reload --port 8000
```

Frontend (React + Vite) — quick run

1. Install dependencies and start dev server:

```bash
cd frontend/web
npm install
npm run dev
```

Notes

- The prototype uses read-only DB views. Create local SQL views under `backend/app/db/views.sql` and apply them against a dev copy of the database.
- For exports over 10k rows, the API will accept the request and generate an async export; the quickstart demonstrates synchronous small exports.
