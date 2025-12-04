# Implementation Plan: Ingestion Dashboard

**Branch**: `003-ingestion-dashboard` | **Date**: 2025-12-04 | **Spec**: `specs/003-ingestion-dashboard/spec.md`
**Input**: Feature specification from `specs/003-ingestion-dashboard/spec.md`

## Summary

Build an operational dashboard that reads ingestion pipeline data from the existing PostgreSQL (Supabase) database and provides KPIs, detailed lists, drill-downs to raw JSON and normalized records, time-series trend visualisations, structured error logs, alerts, and export functionality. Implementation approach for an MVP:

- Backend: Python FastAPI service that exposes a small, secured read-only API layer and export endpoints.
- Data access: read-only database views and materialised summary views for KPIs (refresh cadence aligned to 5-minute SLA).
- Frontend: React (Vite) single-page app using component library (MUI) and charting (Recharts or Chart.js) for interactive visualisations.
- Deployment: Containerised backend and frontend; can run locally for development and be deployed to Cloud Run / Docker host for production. Authentication delegated to platform (e.g., Supabase Auth or existing SSO) via JWT.

## Technical Context

**Language/Version**: Python 3.11 (matches repo), Node.js 18+ for frontend  
**Primary Dependencies**: `fastapi`, `asyncpg`/`psycopg[binary]`, `sqlalchemy` (optional) for backend; `react`, `vite`, `@mui/material`, `recharts` for frontend  
**Storage**: PostgreSQL (Supabase connection available via `DATABASE_URL` in `.env`)  
**Testing**: `pytest` for backend unit/integration; `playwright`/`jest` for frontend (optional)  
**Target Platform**: Linux container (Docker) — deploy to Cloud Run / ECS / GCP/AWS container service  
**Project Type**: Web application (separate backend API + frontend SPA)  
**Performance Goals**: KPI queries and small list pages should respond <500ms for typical result sizes; chart aggregates for 12 months should render within 2–5s for moderate dataset sizes (up to tens of thousands of rows)  
**Constraints**: Read-only access pattern for production DB; do not perform destructive changes; avoid long-running sync queries on the main DB by using materialised views or read replicas for heavy aggregations.  
**Scale/Scope**: MVP targets internal operations team (tens of users); support exports up to 10k rows synchronously, larger via async batch jobs.

## Constitution Check

Gates: apply the repository constitution template to verify policy compliance. Summary of checks performed:

- Security: ensure secrets are not committed to the repo. (Note: `.env` exists locally — keep out of VCS.)  
- Observability: logging and structured errors are already a project concern (see `services/json_validator.py` / `services/ingestion_service.py`).  
- Testing: integration tests exist in `tests/integration` and follow repo patterns.  

Result: No constitution gates violated by the plan. If a specific gate is raised (e.g., add mandatory integration tests for any new DB view), it will be listed here and must be justified.

## Project Structure

Documentation (this feature)

```text
specs/003-ingestion-dashboard/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (openapi)
└── tasks.md             # Phase 2 output (created later)
```

Source code (proposed layout)

```text
backend/
├── app/
│   ├── main.py          # FastAPI app
│   ├── api/
│   │   ├── kpis.py
│   │   ├── meetings.py
│   │   └── exports.py
│   ├── db/
│   │   ├── views.sql    # read-only DB view definitions (not automatically applied)
│   │   └── connection.py
│   └── services/
└── tests/

frontend/
├── web/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   └── services/api.ts
│   └── package.json
```

**Structure Decision**: Use Option 2 (Web application) — separate `backend/` (FastAPI) and `frontend/web/` (React + Vite). This matches the existing Python codebase and keeps UI concerns isolated.

## Complexity Tracking

No constitution violations detected that require formal justification. If we choose to add a read-replica or change database schema, that will be added here with justification.

## Phase 0: Research (this output is in `research.md`)

See `research.md` for decisions about frontend stack, auth, exports, and data access patterns. Research resolves the remaining NEEDS CLARIFICATION items from the spec.

## Phase 1: Design outputs (to be created)

- `data-model.md` — canonical entity definitions for the dashboard views  
- `contracts/openapi.yaml` — API contract for backend endpoints  
- `quickstart.md` — how to run the prototype locally

---

Next: generate `research.md` (Phase 0) and then create Phase 1 artifacts (`data-model.md`, `contracts/`, `quickstart.md`).
