# Tasks: Ingestion Dashboard (specs/003-ingestion-dashboard)

Phase 1: Setup

- [ ] T001 Create backend scaffold and FastAPI entry `backend/app/main.py`
- [P] T002 Create frontend scaffold (Vite + React) and `frontend/web/package.json`
- [ ] T003 Add read-only DB view definitions file `backend/app/db/views.sql`
- [ ] T004 Add `.env.example` with `DATABASE_URL` placeholder at repository root
- [ ] T005 Add CI skeleton for dashboard `.github/workflows/dashboard-ci.yml`

Phase 2: Foundational (blocking prerequisites)

- [ ] T006 Create materialised-view SQL `backend/app/db/materialized_views.sql` for KPI aggregates
- [ ] T007 Implement DB connection module `backend/app/db/connection.py`
- [ ] T008 Implement authentication/authorization helper `backend/app/api/auth.py` (JWT role checks)
- [P] T009 Implement API router registration in `backend/app/main.py` (mount `/api`)
- [ ] T010 Add DB migration / seed script for local dev `scripts/setup_dashboard_dev_db.sh`

Phase 3: User Story Phases (priority order)

US1: Operational Overview (Priority: P1)

- [ ] T011 [US1] [P] Implement KPI API endpoint in `backend/app/api/kpis.py` returning KPIs (total_ingested, sources_count, success_rate, duplicates_avoided, last_run_timestamp)
- [ ] T012 [US1] Create materialised view `mv_ingestion_kpis` referenced by `backend/app/db/materialized_views.sql`
- [P] T013 [US1] Implement Alerts API in `backend/app/api/alerts.py` to list recent failures and support ack action for admins
- [ ] T014 [US1] Implement frontend KPI summary component `frontend/web/src/components/Kpis.tsx`
- [ ] T015 [US1] Implement frontend Alerts panel `frontend/web/src/components/Alerts.tsx` and admin ack action
- [ ] T016 [US1] Write integration test for KPI endpoints `tests/integration/test_kpis.py`

US2: Investigation & Drill-down (Priority: P1)

- [ ] T017 [US2] Implement meetings list API in `backend/app/api/meetings.py` with pagination and filtering (workgroup, source, date range, search)
- [ ] T018 [US2] Implement meeting detail API `backend/app/api/meetings.py` -> `GET /meetings/{id}` returning raw JSON and normalized fields
- [ ] T019 [US2] Implement frontend Meetings List page `frontend/web/src/pages/MeetingsList.tsx` with filters and pagination
- [P] T020 [US2] Implement frontend Meeting Detail view `frontend/web/src/pages/MeetingDetail.tsx` showing raw JSON, normalized fields, warnings, and provenance
- [ ] T021 [US2] Implement export endpoint for filtered meetings `backend/app/api/exports.py` (CSV/JSON small sync, async for >10k)
- [ ] T022 [US2] Add unit/integration tests for meetings endpoints `tests/integration/test_meetings.py`

US3: Trend Visualisation & Exports (Priority: P2)

- [ ] T023 [US3] Implement ingestion runs API in `backend/app/api/runs.py` and materialised monthly aggregates `mv_ingestion_monthly`
- [P] T024 [US3] Implement frontend Trends page `frontend/web/src/pages/Trends.tsx` with charts (ingestion volume per month, failure rate)
- [ ] T025 [US3] Implement export task manager `backend/app/services/export_manager.py` for async exports and download links
- [ ] T026 [US3] Add integration tests for trends and export flows `tests/integration/test_trends_exports.py`

Phase 4: Polish & Cross-cutting Concerns

- [ ] T027 [P] Add role-based UI controls (hide ack buttons for Read-only) in `frontend/web/src/components/*`
- [ ] T028 Add logging and structured error responses in backend `backend/app/main.py` and `backend/app/api/*`
- [ ] T029 Add quickstart updates `specs/003-ingestion-dashboard/quickstart.md` with exact scaffold run commands (ensure accuracy)
- [ ] T030 Add end-to-end smoke test `tests/integration/test_e2e_dashboard.py` exercising deployable app locally (kpis -> meetings -> export)
- [ ] T031 Document DB view maintenance and refresh schedule `specs/003-ingestion-dashboard/data-model.md` (add CRON example)
- [ ] T032 Prepare deployment manifest `deploy/dashboard/Dockerfile` and `deploy/dashboard/docker-compose.yml`
- [ ] T033 Add security review checklist `specs/003-ingestion-dashboard/checklists/security.md`

Final Phase: Release & Handoff

- [ ] T034 Create PR with draft release notes and reviewer checklist `PULL_REQUEST_TEMPLATE.md` (or use GitHub PR description)
- [ ] T035 Add monitoring/alerting runbook snippet `docs/operations/ingestion-dashboard-runbook.md`

Notes on parallelization and ordering

- Tasks marked with `[P]` are parallelizable: frontend scaffolding, independent endpoints, and component implementations can proceed in parallel as long as API contracts are respected.
- Story-phase tasks depend on foundational Phase 2 tasks (DB views, DB connection, auth) before full end-to-end tests.

*** End Patch