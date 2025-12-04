```markdown
# Feature Specification: Ingestion Dashboard

**Feature Branch**: `003-ingestion-dashboard`  
**Created**: 2025-12-04  
**Status**: Draft  
**Input**: User description: "Build a web-dashboard for the SingularityNET-Archive data-ingestion pipeline that connects to the underlying PostgreSQL (or Supabase) database and provides interactive, real-time (or near real-time) views of ingestion status, data health, and metadata. The dashboard should display high-level metrics (e.g. total number of meeting summaries ingested, number of sources processed, ingestion success vs failure rate, number of duplicates avoided via UPSERTs, last ingestion run timestamp, error counts), plus more detailed views (e.g. list of ingested meetings, with workgroup, date, and any validation warnings or missing fields, ability to filter by year/source/workgroup, and drill down to raw JSON or normalized records). It should also visualise trends over time (e.g. ingestion volume per month, failure rate over time) and surface alerts for recent failures or schema-validation errors. Logging data (structured error logs with source URL, error type/message, timestamp) should be accessible for debugging. The UI should allow both summary (KPIs) and detailed investigatory work, with export functionality (CSV/JSON) for downstream analysis."

## Summary

Build a web-based dashboard that provides operational visibility into the data-ingestion pipeline. The dashboard connects to the project's primary datastore (PostgreSQL or Supabase) and presents both high-level KPIs and detailed investigative views for ingested meeting summaries and ingestion runs. It must support filtering, drill-down to raw JSON and normalized records, trend visualisations, and access to structured error logs. Export (CSV/JSON) and alerting for recent failures or schema-validation issues are required.

## Actors, Actions, Data, Constraints

- Actors: **Ops engineer / Data steward**, **Developer**, **Project manager / Stakeholder** (read-only analytics)
- Actions: view KPIs, filter and search ingested meetings, drill down to raw JSON, export results, view and filter error logs, acknowledge alerts
- Data: meeting summaries (raw JSON + normalized fields), ingestion run records, validation warnings, structured error logs, source metadata
- Constraints: read-only access to production data unless explicitly authorized; near-real-time view defined by acceptable latency (see Assumptions)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Operational Overview (Priority: P1)

As an **Ops engineer**, I want a single dashboard showing up-to-date KPIs so I can quickly assess ingestion health and spot failures.

**Why this priority**: Operational visibility prevents prolonged outages and reduces mean time to repair.

**Independent Test**: With sample ingestion data, confirm dashboard shows totals and rates matching database queries over the same time window.

**Acceptance Scenarios**:
1. **Given** ingestion data exists, **When** I open the dashboard, **Then** I see KPIs including total ingested count, number of sources, success vs failure rate, duplicates avoided, last run timestamp, and error counts.
2. **Given** a recent failed ingestion, **When** I open the alerts panel, **Then** the failure appears with a link to the related error log and ingestion run.

---

### User Story 2 - Investigation & Drill-down (Priority: P1)

As a **Developer or Data Steward**, I want to list ingested meetings, filter by year/source/workgroup, and drill down to raw JSON and normalized fields so I can debug data quality issues.

**Why this priority**: Enables root-cause analysis of validation errors and pipeline problems.

**Independent Test**: Run a filtered query and verify returned rows match DB; open a record and confirm raw JSON and normalized fields render correctly.

**Acceptance Scenarios**:
1. **Given** multiple ingested records, **When** I filter by workgroup and year, **Then** only matching records are listed.
2. **Given** a listed record with validation warnings, **When** I open details, **Then** I see the raw JSON, normalized fields, and any validation warnings.

---

### User Story 3 - Trend Visualisation & Exports (Priority: P2)

As a **Project Manager**, I want to view ingestion volume and failure rate trends over time and export data so I can report on pipeline performance.

**Why this priority**: Provides business-level insight and enables offline analysis.

**Independent Test**: Generate time-series charts from stored runs and verify CSV/JSON export contains the same aggregated numbers.

**Acceptance Scenarios**:
1. **Given** ingestion history, **When** I view the trends page for the last 12 months, **Then** I see a time-series of ingested volume per month and failure rate per month.
2. **Given** a filtered result set, **When** I request export, **Then** a CSV and JSON download are produced and include the displayed fields.

---

### Edge Cases

- Large result sets: exporting or listing thousands of records should be paginated and provide server-side export to avoid UI timeouts.
- Partially normalized records (missing fields): show missing-field indicators and surface validation warnings per record.
- Concurrent ingestion runs: ensure last-run timestamp and run details clearly identify which run produced which records.

## Requirements *(mandatory)*

### Functional Requirements (each requirement is testable)

- **FR-001**: Dashboard MUST display KPIs: total meeting summaries ingested (all time and within selectable window), number of distinct sources processed, ingestion success vs failure rate (percentage), number of duplicates avoided (UPSERT count), timestamp of last ingestion run, and current error count.
- **FR-002**: Dashboard MUST provide a paginated list view of ingested meetings with columns: `id`, `workgroup`, `source`, `ingested_at` (timestamp), `date` (meeting date), `validation_warnings_count` and an indicator for missing mandatory fields.
- **FR-003**: Dashboard MUST allow filtering the list by date range, year, source, and workgroup, and allow free-text search over workgroup and title fields.
- **FR-004**: Dashboard MUST allow drilling into an individual record to view raw JSON, normalized fields, and any validation warnings or error messages.
- **FR-005**: Dashboard MUST provide trend visualisations: ingestion volume per configurable time bucket (day/week/month) and failure rate over time for a selectable time range.
- **FR-006**: Dashboard MUST surface alerts for recent failures and schema-validation errors, including a link from the alert to the associated ingestion run and error log entry.
- **FR-007**: Dashboard MUST provide access to structured error logs (fields: `timestamp`, `source_url`, `error_type`, `message`, `ingestion_run_id`) with filtering by time range, error type, and source.
- **FR-008**: Dashboard MUST support export of list and filtered views to CSV and JSON with fields matching the UI table and detail view.
- **FR-009**: Dashboard MUST show provenance metadata for each record where available (original source URL, downloader id, and ingestion run id).
- **FR-010**: Dashboard MUST include role-based view constraints with two roles defined:
  - **Read-only**: can view Operational Overview KPIs, list and detail views, access and filter structured error logs, download/export CSV/JSON, and view trend visualisations. Read-only users cannot acknowledge alerts or access admin-only links.
  - **Admin**: all Read-only permissions plus the ability to acknowledge/clear alerts, access ingestion-run internal links for debugging, and perform dashboard administrative actions (e.g., trigger manual re-checks or request exports on behalf of users).

### Key Entities *(data model level, non-implementation)*

- **MeetingSummary**: Represents an ingested meeting summary. Key attributes: `id`, `source_id`, `workgroup`, `meeting_date`, `ingested_at`, `normalized_fields` (list), `raw_json_reference`, `validation_warnings_count`, `provenance`.
- **Source**: Represents an ingestion source. Key attributes: `id`, `name`, `type`, `last_polled_at`.
- **IngestionRun**: Represents a pipeline run. Key attributes: `id`, `started_at`, `finished_at`, `status` (success/failure), `records_processed`, `records_failed`, `duplicates_avoided`.
- **ValidationWarning**: Represents a schema or content validation issue attached to a `MeetingSummary`. Key attributes: `code`, `message`, `field_path`.
- **ErrorLog**: Structured errors emitted during ingestion. Key attributes: `timestamp`, `source_url`, `error_type`, `message`, `ingestion_run_id`, `raw_payload_reference`.

## Assumptions

- The dashboard reads data directly from the existing PostgreSQL (or Supabase) schema used by the ingestion pipeline.
- "Near real-time" is assumed to mean data visible within 5 minutes of ingestion unless otherwise specified.
- Authentication and authorization will be provided by the platform/environment; the spec assumes a mechanism for role-based access control exists. Two default roles are defined: `read-only` and `admin` (see FR-010).
- Exports are snapshot exports; very large exports may be delivered asynchronously (accepted-but-processed model).

## Success Criteria *(mandatory & measurable)*

- **SC-001**: Users can view the Operational Overview dashboard where the displayed KPIs match the results from authoritative database queries within ±1% for aggregated counts, for sampled datasets.
- **SC-002**: Users can filter the ingested meetings list and see correct filtered counts and records for at least 95% of test queries (functional correctness for filtering/search).
- **SC-003**: Trend charts render for a 12-month window and match aggregated results from ingestion run records; chart load time for typical 12-month data is under 5 seconds in normal network conditions.
- **SC-004**: Alerts for failures appear in the UI within the configured data latency window (default: 5 minutes) after a failure is recorded in the DB.
- **SC-005**: Exports (CSV/JSON) for filtered result sets up to 10,000 rows complete successfully and contain the same columns and values as the UI table.
- **SC-006**: Error logs are searchable and filterable by time range and error type, and each error entry links to the associated ingestion run and, where applicable, the offending raw payload.

## Testing & Verification

- Provide a test dataset of ingested records including successful, failed, duplicate, and partially-normalized records.
- Verify KPI counts directly against SQL queries run against the same database snapshots.
- Validate that filtering, pagination, drill-down, exports, and charts behave as documented in acceptance scenarios.

## Non-Goals / Out of Scope

- This spec does not define authentication/SSO implementation details or production deployment topology.
- This spec does not include building new ingestion processes or changing the existing database schema (unless small, additive view tables are required; see Assumptions).

## Implementation Notes (for planning only)

- Prefer adding read-only database views or materialised summaries if needed for performant KPIs (decided during planning).
- Consider rate limits on exports and background jobs for large dataset exports.

## Clarifications

### Session 2025-12-04

- Q: Q1 - Access Control → A: Option A - Read-only + Admin (Read-only users can view KPIs, lists, error logs, and export; Admins can also acknowledge alerts, view internal links, and perform admin-only actions). Applied to `FR-010` and Assumptions.

- Q: Q2 - Data Latency SLA → A: Option B - 5 minutes (Default). Dashboard data should be considered "near real-time" if visible within 5 minutes of ingestion; reflected in Assumptions and `SC-004`.


## Questions / Clarifications (max 3)

1. **Q1 - Access Control**: Which user roles should exist and what permissions should each role have? (Options: A) Read-only (Ops/Stakeholder) + Admin (full access incl. acknowledgements) B) Read-only only C) Custom - provide role definitions)
2. **Q2 - Data Latency SLA**: Is the default "near real-time" target of 5 minutes acceptable, or should it be tighter/looser? (Options: A) 1 minute, B) 5 minutes (default), C) 30 minutes)

Replace these markers with chosen answers before proceeding to planning.

---

**Prepared by**: speckit.specify

```# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`  
**Created**: [DATE]  
**Status**: Draft  
**Input**: User description: "$ARGUMENTS"

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - [Brief Title] (Priority: P1)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently - e.g., "Can be fully tested by [specific action] and delivers [specific value]"]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]
2. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

### User Story 2 - [Brief Title] (Priority: P2)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

### User Story 3 - [Brief Title] (Priority: P3)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

[Add more user stories as needed, each with an assigned priority]

### Edge Cases

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right edge cases.
-->

- What happens when [boundary condition]?
- How does system handle [error scenario]?

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST [specific capability, e.g., "allow users to create accounts"]
- **FR-002**: System MUST [specific capability, e.g., "validate email addresses"]  
- **FR-003**: Users MUST be able to [key interaction, e.g., "reset their password"]
- **FR-004**: System MUST [data requirement, e.g., "persist user preferences"]
- **FR-005**: System MUST [behavior, e.g., "log all security events"]

*Example of marking unclear requirements:*

- **FR-006**: System MUST authenticate users via [NEEDS CLARIFICATION: auth method not specified - email/password, SSO, OAuth?]
- **FR-007**: System MUST retain user data for [NEEDS CLARIFICATION: retention period not specified]

### Key Entities *(include if feature involves data)*

- **[Entity 1]**: [What it represents, key attributes without implementation]
- **[Entity 2]**: [What it represents, relationships to other entities]

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: [Measurable metric, e.g., "Users can complete account creation in under 2 minutes"]
- **SC-002**: [Measurable metric, e.g., "System handles 1000 concurrent users without degradation"]
- **SC-003**: [User satisfaction metric, e.g., "90% of users successfully complete primary task on first attempt"]
- **SC-004**: [Business metric, e.g., "Reduce support tickets related to [X] by 50%"]
