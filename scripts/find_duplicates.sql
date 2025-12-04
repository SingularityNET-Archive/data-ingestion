-- ============================================================================
-- DUPLICATE DETECTION QUERIES
-- ============================================================================
-- This script identifies duplicate records across all tables by checking
-- for multiple rows with the same UUID (which should be impossible with
-- proper PRIMARY KEY constraints) or multiple rows with identical content
-- that should have the same deterministic UUID.
--
-- Run this to investigate duplicate insertion issues.
-- ============================================================================

-- Check for duplicate UUIDs (should never happen with PRIMARY KEY)
-- If this returns any rows, the PRIMARY KEY constraint is missing or broken
SELECT 
    'workgroups' as table_name,
    id,
    COUNT(*) as duplicate_count,
    array_agg(created_at ORDER BY created_at) as creation_times,
    array_agg(updated_at ORDER BY updated_at) as update_times
FROM workgroups
GROUP BY id
HAVING COUNT(*) > 1;

SELECT 
    'meetings' as table_name,
    id,
    COUNT(*) as duplicate_count,
    array_agg(created_at ORDER BY created_at) as creation_times,
    array_agg(updated_at ORDER BY updated_at) as update_times,
    array_agg(workgroup_id) as workgroup_ids,
    array_agg(date) as dates
FROM meetings
GROUP BY id
HAVING COUNT(*) > 1;

SELECT 
    'agenda_items' as table_name,
    id,
    COUNT(*) as duplicate_count,
    array_agg(created_at ORDER BY created_at) as creation_times,
    array_agg(updated_at ORDER BY updated_at) as update_times,
    array_agg(meeting_id) as meeting_ids
FROM agenda_items
GROUP BY id
HAVING COUNT(*) > 1;

SELECT 
    'action_items' as table_name,
    id,
    COUNT(*) as duplicate_count,
    array_agg(created_at ORDER BY created_at) as creation_times,
    array_agg(updated_at ORDER BY updated_at) as update_times,
    array_agg(agenda_item_id) as agenda_item_ids
FROM action_items
GROUP BY id
HAVING COUNT(*) > 1;

SELECT 
    'decision_items' as table_name,
    id,
    COUNT(*) as duplicate_count,
    array_agg(created_at ORDER BY created_at) as creation_times,
    array_agg(updated_at ORDER BY updated_at) as update_times,
    array_agg(agenda_item_id) as agenda_item_ids
FROM decision_items
GROUP BY id
HAVING COUNT(*) > 1;

SELECT 
    'discussion_points' as table_name,
    id,
    COUNT(*) as duplicate_count,
    array_agg(created_at ORDER BY created_at) as creation_times,
    array_agg(updated_at ORDER BY updated_at) as update_times,
    array_agg(agenda_item_id) as agenda_item_ids
FROM discussion_points
GROUP BY id
HAVING COUNT(*) > 1;

-- ============================================================================
-- Check for meetings with same workgroup_id + date + host + purpose
-- (these should have the same deterministic UUID)
-- ============================================================================
SELECT 
    'meetings_same_content' as check_type,
    workgroup_id,
    date,
    host,
    purpose,
    COUNT(DISTINCT id) as unique_ids,
    array_agg(DISTINCT id) as meeting_ids,
    array_agg(created_at ORDER BY created_at) as creation_times
FROM meetings
GROUP BY workgroup_id, date, host, purpose
HAVING COUNT(DISTINCT id) > 1
ORDER BY COUNT(DISTINCT id) DESC;

-- ============================================================================
-- Check for agenda items with same meeting_id + order_index
-- (these should have the same deterministic UUID)
-- ============================================================================
SELECT 
    'agenda_items_same_content' as check_type,
    meeting_id,
    order_index,
    COUNT(DISTINCT id) as unique_ids,
    array_agg(DISTINCT id) as agenda_item_ids,
    array_agg(created_at ORDER BY created_at) as creation_times
FROM agenda_items
GROUP BY meeting_id, order_index
HAVING COUNT(DISTINCT id) > 1
ORDER BY COUNT(DISTINCT id) DESC;

-- ============================================================================
-- Check for action items with same agenda_item_id + text
-- (these should have the same deterministic UUID if order is preserved)
-- ============================================================================
SELECT 
    'action_items_same_content' as check_type,
    agenda_item_id,
    text,
    COUNT(DISTINCT id) as unique_ids,
    array_agg(DISTINCT id) as action_item_ids,
    array_agg(created_at ORDER BY created_at) as creation_times
FROM action_items
GROUP BY agenda_item_id, text
HAVING COUNT(DISTINCT id) > 1
ORDER BY COUNT(DISTINCT id) DESC;

-- ============================================================================
-- Summary: Total counts and potential duplicates
-- ============================================================================
SELECT 
    'summary' as report_type,
    (SELECT COUNT(*) FROM workgroups) as total_workgroups,
    (SELECT COUNT(*) FROM meetings) as total_meetings,
    (SELECT COUNT(*) FROM agenda_items) as total_agenda_items,
    (SELECT COUNT(*) FROM action_items) as total_action_items,
    (SELECT COUNT(*) FROM decision_items) as total_decision_items,
    (SELECT COUNT(*) FROM discussion_points) as total_discussion_points,
    (SELECT COUNT(DISTINCT id) FROM workgroups) as unique_workgroup_ids,
    (SELECT COUNT(DISTINCT id) FROM meetings) as unique_meeting_ids,
    (SELECT COUNT(DISTINCT id) FROM agenda_items) as unique_agenda_item_ids,
    (SELECT COUNT(DISTINCT id) FROM action_items) as unique_action_item_ids,
    (SELECT COUNT(DISTINCT id) FROM decision_items) as unique_decision_item_ids,
    (SELECT COUNT(DISTINCT id) FROM discussion_points) as unique_discussion_point_ids;



