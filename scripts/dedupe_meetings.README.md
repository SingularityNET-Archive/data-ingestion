# Dedupe meetings: preview + transactional run

Files added:

- `scripts/dedupe_meetings_preview.sql` — read-only preview of duplicate meeting groups and per-meeting child counts. Run this first to inspect what will be changed.
- `scripts/dedupe_meetings_run.sql` — transactional script that merges duplicate meeting groups by:
  - keeping the oldest meeting (by `created_at`, tie-break by `id`)
  - reassigning `agenda_items` from duplicate meeting rows to the canonical meeting
  - deleting the duplicate meeting rows

Safety checklist (READ BEFORE RUNNING):

1. Backup your database (pg_dump or snapshot). Example:

```bash
pg_dump --format=custom --file=backup_before_dedupe.dump "$DATABASE_URL"
```

2. Run the preview and inspect the groups (look at `raw_hash`, `agenda_count`, and `created_at` for each member):

```bash
psql "$DATABASE_URL" -f scripts/dedupe_meetings_preview.sql
```

3. If you are satisfied, run the transactional dedupe script. This will modify data.

```bash
psql "$DATABASE_URL" -f scripts/dedupe_meetings_run.sql
```

Notes & caveats:

- The run script creates a temporary backup table `tmp_backup_meetings` that is session-local. If you want persistent backups of the affected rows, create a permanent table and copy rows from `meetings` for the affected ids (or use the pg_dump above).
- The script reassigns `agenda_items.meeting_id` first, then deletes duplicate `meetings`. This assumes `agenda_items.meeting_id` is the only child relationship that needs reassignment; decision/action/discussion items are attached to `agenda_items`, so they stay with their agenda items.
- If you have additional child tables referencing `meetings` directly, update the run script accordingly to reassign those rows before deletion.
- After verifying the dedupe succeeded, add a unique index to prevent recurrence. Use `CREATE UNIQUE INDEX CONCURRENTLY` in production to avoid long locks:

```sql
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS uniq_meetings_wid_date_host_purpose
  ON meetings (workgroup_id, date, host, purpose);
```

If you want, I can:
- adjust the scripts to only process the top N duplicate groups
- add a persistent backup table and an automatic export of backed-up rows
- prepare a reversible migration that records the mapping (old_id -> keep_id) for auditing

Ask which of those you'd like next.
