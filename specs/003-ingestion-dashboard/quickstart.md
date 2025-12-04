# Quickstart — Ingestion Dashboard

## Prerequisites

- Python 3.11+
- Node.js 18+ and npm/yarn
- PostgreSQL database (or Supabase) with the ingestion pipeline schema
- Access to the project's `DATABASE_URL`

## Backend (FastAPI) Setup

1. **Create a virtual environment and install dependencies:**

```bash
cd /path/to/data-ingestion
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```

2. **Set up environment variables:**

Create a `.env` file in the project root (copy from `.env.example` if available):

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/meeting_summaries

# Authentication (for local dev, bypass auth)
DEV_AUTH_BYPASS=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

3. **Set up database views:**

Run the database setup script to create read-only views and materialized views:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/meeting_summaries \
  ./scripts/setup_dashboard_dev_db.sh
```

Or manually apply the SQL files:

```bash
psql $DATABASE_URL -f backend/app/db/views.sql
psql $DATABASE_URL -f backend/app/db/materialized_views.sql
```

4. **Run the backend:**

```bash
cd backend
python -m app.main
# Or with uvicorn directly:
uvicorn app.main:app --reload --port 8000
```

The API will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/healthz

## Frontend (React + Vite) Setup

1. **Install dependencies:**

```bash
cd frontend/web
npm install
```

2. **Configure API endpoint (if needed):**

The frontend defaults to `http://localhost:8000` for the API. To change this, edit `frontend/web/src/services/api.js` and update the `API_BASE_URL`.

3. **Start the development server:**

```bash
npm run dev
```

The frontend will be available at http://localhost:5173 (or the port shown in the terminal).

## Quick Test

1. **Backend health check:**
   ```bash
   curl http://localhost:8000/healthz
   # Should return: {"status":"ok"}
   ```

2. **Get KPIs:**
   ```bash
   curl http://localhost:8000/api/kpis
   # Should return JSON with KPI metrics
   ```

3. **Open the dashboard:**
   - Navigate to http://localhost:5173 in your browser
   - You should see the Operational Overview with KPIs and Alerts

## Notes

- **Database Views**: The dashboard uses read-only views defined in `backend/app/db/views.sql`. These views must be created before the dashboard can function.
- **Materialized Views**: KPI queries use materialized views that should be refreshed periodically (every 3-5 minutes). See `backend/app/db/refresh_materialized_views.sh` for a refresh script.
- **Authentication**: For local development, set `DEV_AUTH_BYPASS=true` to bypass JWT authentication. **Never enable this in production!**
- **Large Exports**: Exports over 10,000 rows will return a 413 error. For larger exports, implement async export processing using the `export_manager.py` service.
- **CORS**: The backend is configured to allow CORS from any origin. In production, restrict this to your frontend domain.

## Troubleshooting

- **"DATABASE_URL not configured"**: Ensure `.env` file exists and contains `DATABASE_URL`
- **"View does not exist"**: Run the database setup script to create views
- **"Connection refused"**: Check that PostgreSQL is running and `DATABASE_URL` is correct
- **Frontend can't connect to API**: Verify backend is running on port 8000 and check CORS settings
