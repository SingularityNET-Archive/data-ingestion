# Supabase Quick Start Checklist

Use this checklist to quickly set up Supabase for the ingestion pipeline.

## ✅ Setup Checklist

- [ ] **Step 1**: Create Supabase project at https://app.supabase.com
- [ ] **Step 2**: Get database connection string (Settings → Database → Connection string)
- [ ] **Step 3**: Create database schema (SQL Editor → Run `scripts/setup_db.sql`)
- [ ] **Step 4**: Add GitHub Secret `SUPABASE_DATABASE_URL` with connection string
- [ ] **Step 5**: Verify workflow file exists (`.github/workflows/ingest-meetings.yml`)
- [ ] **Step 6**: Test workflow (Actions → Run workflow → Manual trigger)
- [ ] **Step 7**: Verify data in Supabase (Table Editor → Check tables)

## Quick Commands

### Get Connection String
1. Supabase Dashboard → Settings → Database
2. Copy "Connection string" (URI tab)
3. Replace `[YOUR-PASSWORD]` with your actual password

### Create Schema
1. Supabase Dashboard → SQL Editor → New query
2. Copy contents of `scripts/setup_db.sql`
3. Paste and Run

### Configure GitHub Secret
1. GitHub Repository → Settings → Secrets → Actions
2. New repository secret
3. Name: `SUPABASE_DATABASE_URL`
4. Value: Your connection string

### Test Workflow
1. GitHub Repository → Actions tab
2. Select "Ingest Meeting Summaries"
3. Click "Run workflow"
4. Monitor execution

## Expected Results

After successful ingestion:
- **Workgroups**: ~10-20 records
- **Meetings**: ~677 records
- **Agenda Items**: Various counts
- **Action Items**: Various counts
- **Decision Items**: Various counts
- **Discussion Points**: Various counts

## Need Help?

See `SUPABASE_SETUP_GUIDE.md` for detailed step-by-step instructions.



