# Duplicate Insertion Diagnosis Guide

This document outlines the potential causes of duplicate records and provides tools to diagnose and fix them.

## Potential Causes

### 1. ✅ FIXED: Concurrent Workflow Runs (Race Conditions)

**Issue**: Multiple GitHub Actions workflow runs could execute simultaneously, causing race conditions where two processes try to insert the same records at the same time.

**Status**: **FIXED** - Added concurrency control to `.github/workflows/ingest-meetings.yml`:
```yaml
concurrency:
  group: ingest-meetings
  cancel-in-progress: false  # Wait for current run to finish
```

**Verification**: Check GitHub Actions runs to ensure no overlapping executions.

---

### 2. Database Constraints

**Issue**: If PRIMARY KEY constraints are missing or broken, duplicate UUIDs could be inserted.

**Status**: Schema defines PRIMARY KEY constraints on all `id` columns. Verify they exist in your database.

**Check**: Run `scripts/check_constraints_and_duplicates.py` to verify constraints.

---

### 3. UPSERT Function Issues

**Issue**: The UPSERT functions use `ON CONFLICT (id) DO UPDATE`, which requires a PRIMARY KEY or UNIQUE constraint on `id`. If the constraint is missing, UPSERT behaves like INSERT.

**Status**: Schema defines UPSERT functions correctly. Verify they exist and are being called.

**Check**: Verify UPSERT functions exist:
```sql
SELECT routine_name 
FROM information_schema.routines 
WHERE routine_schema = 'public' 
  AND routine_name LIKE 'upsert_%';
```

---

### 4. Transaction Isolation Issues

**Issue**: Each meeting is processed in its own transaction. If transactions don't properly isolate, duplicates could occur.

**Status**: Code uses `async with conn.transaction()` which provides proper isolation. However, if multiple ingestion processes run concurrently, they could both read "no existing record" before either commits.

**Mitigation**: Concurrency control (item #1) prevents this.

---

### 5. Nested Entity UUID Generation

**Issue**: Nested entities (action items, decisions, discussion points) use array indices for deterministic UUIDs. If array order changes or items are reordered, different UUIDs could be generated.

**Current Logic**:
- Agenda items: `{meeting_id}:agenda:{idx}`
- Action items: `{agenda_item_id}:action:{action_idx}`
- Decision items: `{agenda_item_id}:decision:{decision_idx}`
- Discussion points: `{agenda_item_id}:discussion:{discussion_idx}`

**Risk**: If source JSON arrays are reordered between runs, different UUIDs will be generated, causing "orphaned" old records and new duplicates.

**Recommendation**: Consider using content-based hashing instead of array indices for nested entities if order can change.

---

### 6. Connection Pool Issues

**Issue**: Connection pool with `max_size=10` could theoretically allow concurrent transactions if code is modified to process meetings in parallel.

**Status**: Current code processes meetings sequentially, so this is not an issue. However, if you modify code to use `asyncio.gather()` or similar, ensure proper locking.

---

## Diagnostic Tools

### 1. Check Constraints and Find Duplicates

Run the comprehensive diagnostic script:

```bash
python scripts/check_constraints_and_duplicates.py
```

This will:
- Verify PRIMARY KEY constraints exist on all tables
- Find duplicate UUIDs (should never happen)
- Find content-based duplicates (same content, different UUIDs)
- Show table statistics

### 2. SQL Query for Manual Investigation

Run the SQL queries in `scripts/find_duplicates.sql` to manually investigate:

```bash
psql $DATABASE_URL -f scripts/find_duplicates.sql
```

---

## Immediate Actions

1. **Run the diagnostic script**:
   ```bash
   export DATABASE_URL="your_database_url"
   python scripts/check_constraints_and_duplicates.py
   ```

2. **Check GitHub Actions runs**:
   - Go to your repository → Actions
   - Verify no overlapping runs
   - Check if the concurrency control is working

3. **Verify database constraints**:
   ```sql
   -- Check PRIMARY KEY constraints
   SELECT 
       tc.table_name,
       tc.constraint_name,
       kcu.column_name
   FROM information_schema.table_constraints tc
   JOIN information_schema.key_column_usage kcu
       ON tc.constraint_name = kcu.constraint_name
   WHERE tc.table_schema = 'public'
     AND tc.constraint_type = 'PRIMARY KEY'
     AND kcu.column_name = 'id'
   ORDER BY tc.table_name;
   ```

4. **Check for duplicate UUIDs**:
   ```sql
   -- This should return 0 rows if constraints are working
   SELECT 'workgroups' as table_name, id, COUNT(*) 
   FROM workgroups GROUP BY id HAVING COUNT(*) > 1
   UNION ALL
   SELECT 'meetings', id, COUNT(*) 
   FROM meetings GROUP BY id HAVING COUNT(*) > 1
   UNION ALL
   SELECT 'agenda_items', id, COUNT(*) 
   FROM agenda_items GROUP BY id HAVING COUNT(*) > 1
   UNION ALL
   SELECT 'action_items', id, COUNT(*) 
   FROM action_items GROUP BY id HAVING COUNT(*) > 1
   UNION ALL
   SELECT 'decision_items', id, COUNT(*) 
   FROM decision_items GROUP BY id HAVING COUNT(*) > 1
   UNION ALL
   SELECT 'discussion_points', id, COUNT(*) 
   FROM discussion_points GROUP BY id HAVING COUNT(*) > 1;
   ```

---

## Prevention Measures

### ✅ Implemented

1. **Concurrency Control**: GitHub Actions workflow now prevents overlapping runs
2. **Diagnostic Tools**: Scripts to identify and diagnose duplicates
3. **Transaction Isolation**: Each meeting processed in its own transaction

### 🔄 Recommended (if issues persist)

1. **Add Advisory Locks**: Use PostgreSQL advisory locks to prevent concurrent ingestion:
   ```python
   # In ingestion_service.py, before processing meetings:
   lock_id = 12345  # Arbitrary lock ID
   await conn.execute("SELECT pg_advisory_lock($1)", lock_id)
   try:
       # Process meetings
   finally:
       await conn.execute("SELECT pg_advisory_unlock($1)", lock_id)
   ```

2. **Content-Based UUIDs for Nested Entities**: If array order can change, use content hashing instead of indices.

3. **Idempotency Checks**: Before inserting, check if record exists and skip if identical:
   ```python
   existing = await conn.fetchrow(
       "SELECT id FROM meetings WHERE id = $1", meeting_id
   )
   if existing:
       # Compare content hash, skip if identical
       pass
   ```

---

## Next Steps

1. Run `scripts/check_constraints_and_duplicates.py` to identify current duplicates
2. Review GitHub Actions logs for overlapping runs
3. If duplicates exist, determine their pattern:
   - Same UUID multiple times? → Constraint issue
   - Same content, different UUIDs? → UUID generation issue
   - Random duplicates? → Race condition or concurrent runs

4. Based on findings, implement appropriate fixes from the recommendations above.


