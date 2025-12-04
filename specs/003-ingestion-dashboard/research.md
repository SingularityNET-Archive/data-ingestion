# Research: Ingestion Dashboard (Phase 0)

Date: 2025-12-04

This document resolves technical unknowns and records decisions and alternatives.

1) Frontend stack
- Decision: Use React + Vite for the frontend SPA, with MUI for components and Recharts (or Chart.js) for charts.
- Rationale: The repository is Python-based; a React SPA provides the richest interactive UX (filtering, drill-down, exports). Vite gives fast dev server and small build. MUI speeds up UI development.
- Alternatives considered:
  - Streamlit: much faster to prototype but limited for polished, role-controlled UIs and exports; not selected for the long-term dashboard.
  - Next.js: good for SSR/SEO but unnecessary for internal ops SPA.

2) Backend framework
- Decision: FastAPI (Python) for the backend API.
- Rationale: Repo is Python-first; FastAPI provides async endpoints, automatic OpenAPI generation, and good performance. It integrates easily with async DB drivers.
- Alternatives: Flask (synchronous), but FastAPI better for modern async DB access and OpenAPI.

3) Authentication / Authorization
- Decision: Integrate with existing platform auth (Supabase Auth or existing SSO) using JWTs. Implement role-checks in the API for `read-only` vs `admin` enforced server-side.
- Rationale: The spec assumes platform auth; reusing Supabase Auth or the org SSO is simpler and centralises access control.
- Notes: For local development, support a dev-only env var to bypass auth or use a simple token.

4) Data access pattern & KPI aggregation
- Decision: Create read-only DB views and materialised summary views for KPI queries. Schedule refreshes aligned to a 5-minute SLA (e.g., cron job or DB-side refresh every 3–5 minutes). Use the `views.sql` under `backend/app/db/` as source-of-truth definitions.
- Rationale: Aggregates can be expensive; materialised views avoid heavy runtime computation and respect read-only constraint.
- Alternatives: direct ad-hoc queries each request (may overload primary DB), use a read-replica (operational overhead). Materialised views give good tradeoff.

5) Exports
- Decision: Support synchronous CSV/JSON exports up to 10k rows via API. For larger exports, use an async background worker (FastAPI background task + write to object storage) and provide a download link.
- Rationale: Matches SC-005 and keeps UI responsive.

6) Alerts
- Decision: Surface recent failures based on `error_logs` table; alerts displayed in UI and link to ingestion run and error entry. Admins can acknowledge alerts via a small API which records ack metadata.

7) Observability & Logging
- Decision: Backend logs structured events; errors and stack traces go to existing logging pipeline. Dashboard UI will include links to raw payload stored in DB or object storage when available.

8) Deployment
- Decision: Containerised backend and frontend. For MVP: deploy to Cloud Run / Heroku / AWS Fargate. For internal-only dashboard, a small cloud container is acceptable.

Summary of Resolutions
- Frontend: React + Vite + MUI + Recharts
- Backend: FastAPI (Python 3.11)
- Auth: Supabase Auth / existing SSO via JWT, server-side role checks
- Data access: read-only views + materialised summary views, refresh schedule 3–5 minutes to meet SLA
- Exports: sync up to 10k rows; async for larger
- Alerts: use `error_logs` table; Admins can ack via API
