-- Preview duplicate meeting groups and planned actions (DRY RUN)
-- Usage (dry-run):
-- psql "$DATABASE_URL" -f scripts/dedupe_meetings_preview.sql

-- Show top duplicate groups by number of duplicates (limit adjustable)
WITH dup_groups AS (
  SELECT workgroup_id, date, host, purpose, COUNT(*) AS cnt
  FROM meetings
  GROUP BY workgroup_id, date, host, purpose
  HAVING COUNT(*) > 1
  ORDER BY cnt DESC
  LIMIT 20
)
SELECT
  g.workgroup_id,
  g.date,
  g.host,
  g.purpose,
  g.cnt,
  json_agg(json_build_object(
    'id', m.id,
    'created_at', m.created_at,
    'raw_hash', md5(m.raw_json::text),
    'agenda_count', (SELECT COUNT(*) FROM agenda_items a WHERE a.meeting_id = m.id)
  ) ORDER BY m.created_at NULLS FIRST, m.id) AS members
FROM meetings m
JOIN dup_groups g
  ON m.workgroup_id = g.workgroup_id
  AND m.date = g.date
  AND m.host = g.host
  AND m.purpose = g.purpose
GROUP BY g.workgroup_id, g.date, g.host, g.purpose, g.cnt
ORDER BY g.cnt DESC;

-- Per-duplicate-id child counts for inspection (useful to detect subtle differences)
-- Limit to top 200 duplicate meeting ids
SELECT m.id AS meeting_id,
  md5(m.raw_json::text) AS raw_hash,
  m.created_at,
  (SELECT COUNT(*) FROM agenda_items a WHERE a.meeting_id = m.id) AS agenda_count,
  (SELECT COUNT(*) FROM decision_items d JOIN agenda_items ai ON d.agenda_item_id = ai.id WHERE ai.meeting_id = m.id) AS decision_count,
  (SELECT COUNT(*) FROM action_items ai JOIN agenda_items a2 ON ai.agenda_item_id = a2.id WHERE a2.meeting_id = m.id) AS action_count,
  (SELECT COUNT(*) FROM discussion_points dp JOIN agenda_items a3 ON dp.agenda_item_id = a3.id WHERE a3.meeting_id = m.id) AS discussion_count
FROM meetings m
WHERE (m.workgroup_id, m.date, m.host, m.purpose) IN (
  SELECT workgroup_id, date, host, purpose FROM meetings GROUP BY workgroup_id, date, host, purpose HAVING COUNT(*) > 1
)
ORDER BY m.workgroup_id, m.date, m.host, m.purpose, m.created_at
LIMIT 200;
