-- Transactional dedupe of duplicate meetings
-- IMPORTANT: BACKUP your DB before running.  Recommended: pg_dump or snapshot.
-- Usage (CAREFUL):
-- psql "$DATABASE_URL" -f scripts/dedupe_meetings_run.sql
-- This script will, for each duplicate meeting group (same workgroup_id, date, host, purpose):
--  - choose one canonical meeting to keep (oldest by created_at, ties by id)
--  - reassign child `agenda_items` from duplicates to the canonical meeting
--  - delete the duplicate meeting rows
-- The script is transactional: it runs all changes inside a single transaction.
-- If you want to process only a subset, edit the initial 'dup_groups' CTE (LIMIT or WHERE).

BEGIN;

-- Temporary backup table (session-local) to keep copies of deleted meetings
CREATE TEMP TABLE tmp_backup_meetings ON COMMIT PRESERVE ROWS AS
  SELECT * FROM meetings WHERE false;

-- Iterate over duplicate groups
DO $$
DECLARE
  g RECORD;
  member_ids uuid[];
  keep_id uuid;
  dup_id uuid;
BEGIN
  FOR g IN
    SELECT workgroup_id, date, host, purpose, array_agg(id ORDER BY created_at NULLS FIRST, id) AS ids
    FROM meetings
    GROUP BY workgroup_id, date, host, purpose
    HAVING COUNT(*) > 1
    ORDER BY COUNT(*) DESC
  LOOP
    member_ids := g.ids;
    keep_id := member_ids[1];
    RAISE NOTICE 'Processing duplicate group workgroup_id=% date=% host=% purpose=% -> keep=% (members=%)', g.workgroup_id, g.date, g.host, g.purpose, keep_id, member_ids;

    -- For each duplicate id (except keep_id), move agenda_items then delete meeting
    FOREACH dup_id IN ARRAY (SELECT unnest(member_ids[2:array_length(member_ids,1)]))
    LOOP
      -- backup the meeting row
      INSERT INTO tmp_backup_meetings SELECT * FROM meetings WHERE id = dup_id;

      -- reassign agenda_items to canonical meeting
      UPDATE agenda_items SET meeting_id = keep_id WHERE meeting_id = dup_id;

      -- If there are any constraints that would prevent deletion, this will raise an error
      DELETE FROM meetings WHERE id = dup_id;

      RAISE NOTICE '  moved children from % -> % and deleted %', dup_id, keep_id, dup_id;
    END LOOP;
  END LOOP;
END$$;

COMMIT;

-- Post-check: show remaining duplicate groups (should be none)
-- Re-run the preview query to verify
SELECT workgroup_id, date, host, purpose, COUNT(*) as cnt
FROM meetings
GROUP BY workgroup_id, date, host, purpose
HAVING COUNT(*) > 1
ORDER BY cnt DESC
LIMIT 50;

-- After you have verified results, create a unique index to prevent recurrence
-- Recommended (run separately, not inside this transaction):
-- CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS uniq_meetings_wid_date_host_purpose
--   ON meetings (workgroup_id, date, host, purpose);
