# Supabase Setup Guide

This guide walks you through setting up Supabase and configuring the GitHub Actions workflow for automated ingestion.

## Prerequisites

- GitHub account with access to your repository
- Supabase account (sign up at https://supabase.com if needed)

---

## Step 1: Create Supabase Project

1. **Log in to Supabase**
   - Go to [https://app.supabase.com](https://app.supabase.com)
   - Sign in or create an account

2. **Create New Project**
   - Click **New Project**
   - Fill in project details:
     - **Name**: Choose a name (e.g., "meeting-summaries")
     - **Database Password**: Create a strong password (save this securely!)
     - **Region**: Choose closest region to your users
     - **Pricing Plan**: Select Free tier (or paid if needed)

3. **Wait for Project Setup**
   - Project creation takes 1-2 minutes
   - You'll see a progress indicator

---

## Step 2: Get Database Connection String

1. **Navigate to Database Settings**
   - In your Supabase project dashboard
   - Go to **Settings** → **Database**

2. **Find Connection String**
   - Scroll to **Connection string** section
   - Select **URI** tab
   - Copy the connection string
   - Format: `postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres`
   
   **Important**: Replace `[PASSWORD]` with your actual database password

   **Alternative**: Use the **Connection pooling** string (recommended for serverless):
   - Format: `postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres`

3. **Save Connection String**
   - You'll need this for GitHub Secrets in Step 4
   - Example format: `postgresql://postgres.abcdefghijklmnop:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres`

---

## Step 3: Create Database Schema

You need to create the database tables before ingestion can work.

### Option A: Using Supabase SQL Editor (Recommended)

1. **Open SQL Editor**
   - In Supabase dashboard, go to **SQL Editor**
   - Click **New query**

2. **Copy Schema SQL**
   - Open `scripts/setup_db.sql` from your repository
   - Copy the entire contents

3. **Execute SQL**
   - Paste the SQL into the SQL Editor
   - Click **Run** (or press Ctrl+Enter / Cmd+Enter)
   - Wait for execution to complete

4. **Verify Tables Created**
   - Go to **Table Editor** in Supabase dashboard
   - You should see these tables:
     - `workgroups`
     - `meetings`
     - `agenda_items`
     - `action_items`
     - `decision_items`
     - `discussion_points`

### Option B: Using psql Command Line

```bash
# Connect to Supabase database
psql "postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres"

# Execute schema creation
\i scripts/setup_db.sql

# Or copy-paste the SQL directly
```

---

## Step 4: Configure GitHub Secrets

GitHub Actions needs your Supabase connection string to connect to the database.

1. **Navigate to Repository Settings**
   - Go to your GitHub repository
   - Click **Settings** tab
   - In left sidebar, go to **Secrets and variables** → **Actions**

2. **Add New Secret**
   - Click **New repository secret**
   - **Name**: `SUPABASE_DATABASE_URL`
   - **Value**: Paste your Supabase connection string from Step 2
   - Click **Add secret**

3. **Verify Secret Created**
   - You should see `SUPABASE_DATABASE_URL` in the secrets list
   - The value will be masked (shown as dots)

**Security Note**: 
- Never commit connection strings to your repository
- Secrets are encrypted and only accessible to GitHub Actions workflows
- Only repository admins can view/edit secrets

---

## Step 5: Verify GitHub Actions Workflow

The workflow file is already created at `.github/workflows/ingest-meetings.yml`. Verify it exists:

1. **Check Workflow File**
   - Navigate to `.github/workflows/ingest-meetings.yml` in your repository
   - Verify it contains the workflow configuration

2. **Review Workflow Configuration**
   - Schedule: Daily at 2 AM UTC (`cron: '0 2 * * *'`)
   - Manual trigger: Enabled (`workflow_dispatch`)
   - Environment variable: Uses `SUPABASE_DATABASE_URL` secret

---

## Step 6: Test the Workflow

Test the workflow to ensure everything works correctly.

### Option A: Manual Trigger (Recommended for First Test)

1. **Go to Actions Tab**
   - In your GitHub repository, click **Actions** tab

2. **Select Workflow**
   - Click **Ingest Meeting Summaries** workflow (left sidebar)

3. **Run Workflow**
   - Click **Run workflow** dropdown button
   - Select branch (usually `main` or `master`)
   - Click **Run workflow** button

4. **Monitor Execution**
   - You'll see a new workflow run appear
   - Click on it to view real-time logs
   - Watch for any errors

5. **Check Results**
   - Wait for workflow to complete (usually 2-5 minutes)
   - Check logs for success messages
   - Download logs artifact if needed

### Option B: Wait for Scheduled Run

- Workflow runs automatically daily at 2 AM UTC
- Check Actions tab the next day to see the run

---

## Step 7: Verify Data in Supabase

After the workflow runs successfully, verify data was ingested:

1. **Open Supabase Table Editor**
   - Go to Supabase dashboard → **Table Editor**

2. **Check Tables**
   - Click on `workgroups` table
   - You should see workgroup records
   - Check `meetings` table for meeting records
   - Verify other tables have data

3. **Run Verification Query**
   - Go to **SQL Editor**
   - Run this query to see record counts:
   ```sql
   SELECT 
     (SELECT COUNT(*) FROM workgroups) as workgroups,
     (SELECT COUNT(*) FROM meetings) as meetings,
     (SELECT COUNT(*) FROM agenda_items) as agenda_items,
     (SELECT COUNT(*) FROM action_items) as action_items,
     (SELECT COUNT(*) FROM decision_items) as decision_items,
     (SELECT COUNT(*) FROM discussion_points) as discussion_points;
   ```

   Expected results:
   - Workgroups: ~10-20 records
   - Meetings: ~677 records (122 from 2025, 552 from 2024, 2 from 2023, 1 from 2022)
   - Other tables: Various counts based on meeting data

---

## Troubleshooting

### Workflow Fails to Connect to Database

**Symptoms**: Workflow logs show connection errors

**Solutions**:
1. Verify `SUPABASE_DATABASE_URL` secret is set correctly
2. Check connection string format (should start with `postgresql://`)
3. Ensure password in connection string is URL-encoded if it contains special characters
4. Verify Supabase project is active (not paused)

### Workflow Runs But No Data Inserted

**Symptoms**: Workflow completes successfully but tables are empty

**Solutions**:
1. Check workflow logs for validation errors
2. Verify database schema exists (run `scripts/setup_db.sql` again)
3. Check Supabase Table Editor to confirm tables exist
4. Review logs artifact for detailed error messages

### Schema Creation Fails

**Symptoms**: SQL execution errors when creating schema

**Solutions**:
1. Ensure you're using the SQL Editor (not Table Editor)
2. Check for syntax errors in `scripts/setup_db.sql`
3. Verify you have proper permissions (should work with default postgres user)
4. Try running SQL statements one at a time to isolate the issue

### Connection String Issues

**Symptoms**: Cannot connect or authentication fails

**Solutions**:
1. Use **Connection pooling** string (port 6543) instead of direct connection
2. Ensure password doesn't contain unencoded special characters
3. Verify project reference ID is correct
4. Check if project is paused (free tier projects pause after inactivity)

---

## Next Steps After Setup

1. **Monitor Regular Runs**
   - Check Actions tab daily to ensure scheduled runs succeed
   - Set up email notifications for workflow failures (GitHub Settings → Notifications)

2. **Review Data Regularly**
   - Check Supabase Table Editor weekly
   - Verify record counts are increasing as expected
   - Review any error logs

3. **Optimize if Needed**
   - Monitor ingestion performance
   - Adjust workflow timeout if needed (default: 15 minutes)
   - Consider adding monitoring/alerting

4. **Document Your Setup**
   - Note your Supabase project reference ID
   - Save connection string securely (password manager)
   - Document any custom configurations

---

## Security Checklist

- ✅ Database password is strong and unique
- ✅ Connection string stored only in GitHub Secrets (not in code)
- ✅ Supabase project access is restricted to authorized users
- ✅ GitHub repository access is properly configured
- ✅ Workflow logs don't expose sensitive information
- ✅ Regular backups enabled (Supabase handles this automatically)

---

## Support Resources

- **Supabase Documentation**: https://supabase.com/docs
- **GitHub Actions Documentation**: https://docs.github.com/en/actions
- **Project Troubleshooting Guide**: `TROUBLESHOOTING.md`
- **Operations Runbook**: `OPERATIONS_RUNBOOK.md`

---

## Quick Reference

**Supabase Dashboard**: https://app.supabase.com  
**GitHub Actions**: Repository → Actions tab  
**Connection String Location**: Supabase → Settings → Database → Connection string  
**GitHub Secrets**: Repository → Settings → Secrets and variables → Actions  
**Schema File**: `scripts/setup_db.sql`  
**Workflow File**: `.github/workflows/ingest-meetings.yml`

