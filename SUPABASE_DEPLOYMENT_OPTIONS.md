# Supabase Deployment Options (Without Containers)

This document outlines several ways to deploy the ingestion pipeline to work with Supabase **without using containers**.

## Overview

The ingestion pipeline is a pure Python CLI application that can run in various environments. Since Supabase doesn't directly execute Python containers, you have several non-container deployment options.

## Prerequisites

- Supabase database with schema deployed (run `scripts/setup_db.sql`)
- Supabase database connection string
- Python 3.8+ runtime environment
- Network access to GitHub raw content URLs

---

## Option 1: GitHub Actions (Recommended - Free & Simple)

**Best for**: Automated scheduled runs, CI/CD integration, zero infrastructure management

### Setup Steps

1. **Create GitHub Actions Workflow**

Create `.github/workflows/ingest-meetings.yml`:

```yaml
name: Ingest Meeting Summaries

on:
  schedule:
    # Run daily at 2 AM UTC
    - cron: '0 2 * * *'
  workflow_dispatch:  # Allow manual triggers

jobs:
  ingest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run ingestion
        env:
          DATABASE_URL: ${{ secrets.SUPABASE_DATABASE_URL }}
          LOG_FORMAT: json
          LOG_LEVEL: INFO
        run: |
          python -m src.cli.ingest
      
      - name: Upload logs
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: ingestion-logs
          path: ingestion.log
```

2. **Configure Secrets**

In GitHub repository → Settings → Secrets and variables → Actions:
- Add `SUPABASE_DATABASE_URL` secret with your Supabase connection string

3. **Test**

- Push the workflow file
- Go to Actions tab → Run workflow manually
- Verify ingestion completes successfully

### Pros
- ✅ Free for public repos
- ✅ No infrastructure to manage
- ✅ Built-in scheduling
- ✅ Easy to trigger manually
- ✅ Automatic logs/artifacts

### Cons
- ⚠️ Limited to GitHub-hosted runners (public repos free, private repos have limits)
- ⚠️ Runs in ephemeral environment (no persistent state)

---

## Option 2: Serverless Python Functions

### 2A. Google Cloud Functions (Python)

**Best for**: Serverless execution, pay-per-use, Google Cloud ecosystem

#### Setup Steps

1. **Install Google Cloud SDK**

```bash
# Install gcloud CLI
# https://cloud.google.com/sdk/docs/install
```

2. **Create Function**

Create `main.py` in project root:

```python
import os
import asyncio
from src.cli.ingest import _run_ingestion
from src.lib.logger import setup_logger

def ingest_meetings(request):
    """Cloud Function entry point."""
    logger = setup_logger(level="INFO", log_format="json")
    
    default_urls = [
        "https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2025/meeting-summaries-array.json",
        "https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2024/meeting-summaries-array.json",
        "https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2023/meeting-summaries-array.json",
        "https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2022/meeting-summaries-array.json",
    ]
    
    db_url = os.getenv("DATABASE_URL")
    
    asyncio.run(_run_ingestion(default_urls, db_url, False, False, logger))
    
    return {"status": "success", "message": "Ingestion completed"}
```

3. **Deploy Function**

```bash
gcloud functions deploy ingest-meetings \
  --runtime python39 \
  --trigger-http \
  --entry-point ingest_meetings \
  --set-env-vars DATABASE_URL="[SUPABASE_CONNECTION_STRING]" \
  --timeout 540s \
  --memory 512MB
```

4. **Schedule with Cloud Scheduler**

```bash
gcloud scheduler jobs create http ingest-meetings-daily \
  --schedule="0 2 * * *" \
  --uri="https://[REGION]-[PROJECT-ID].cloudfunctions.net/ingest-meetings" \
  --http-method=GET
```

### 2B. AWS Lambda (Python)

**Best for**: AWS ecosystem, serverless execution

#### Setup Steps

1. **Create Lambda Handler**

Create `lambda_handler.py`:

```python
import os
import asyncio
from src.cli.ingest import _run_ingestion
from src.lib.logger import setup_logger

def lambda_handler(event, context):
    """AWS Lambda entry point."""
    logger = setup_logger(level="INFO", log_format="json")
    
    default_urls = [
        "https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2025/meeting-summaries-array.json",
        # ... other URLs
    ]
    
    db_url = os.getenv("DATABASE_URL")
    
    asyncio.run(_run_ingestion(default_urls, db_url, False, False, logger))
    
    return {"statusCode": 200, "body": "Ingestion completed"}
```

2. **Package and Deploy**

```bash
# Install dependencies
pip install -r requirements.txt -t .

# Create deployment package
zip -r function.zip . -x "*.git*" "*.pyc" "__pycache__/*"

# Deploy via AWS CLI or Console
aws lambda create-function \
  --function-name ingest-meetings \
  --runtime python3.9 \
  --role arn:aws:iam::[ACCOUNT]:role/lambda-execution-role \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://function.zip \
  --timeout 900 \
  --memory-size 512 \
  --environment Variables="{DATABASE_URL=[SUPABASE_CONNECTION_STRING]}"
```

3. **Schedule with EventBridge**

Create EventBridge rule to trigger Lambda on schedule (e.g., daily at 2 AM UTC).

### Pros (Serverless Functions)
- ✅ Pay only for execution time
- ✅ Auto-scaling
- ✅ No server management
- ✅ Built-in monitoring

### Cons
- ⚠️ Cold start latency
- ⚠️ Execution time limits (Cloud Functions: 540s, Lambda: 900s)
- ⚠️ May need to optimize for serverless constraints

---

## Option 3: Traditional Server/VM with Cron

**Best for**: Full control, persistent environment, existing infrastructure

### Setup Steps

1. **Provision Server**

- EC2 instance, Google Compute Engine, Azure VM, DigitalOcean Droplet, etc.
- Minimum: 1 CPU, 1GB RAM, Ubuntu 20.04+

2. **Install Python and Dependencies**

```bash
# SSH into server
ssh user@your-server

# Install Python 3.9+
sudo apt update
sudo apt install python3.9 python3-pip python3-venv git

# Clone repository
git clone <your-repo-url>
cd data-ingestion

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

3. **Configure Environment**

```bash
# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
LOG_FORMAT=json
LOG_LEVEL=INFO
EOF

# Secure the file
chmod 600 .env
```

4. **Set Up Cron Job**

```bash
# Edit crontab
crontab -e

# Add daily job at 2 AM UTC
0 2 * * * cd /path/to/data-ingestion && /path/to/venv/bin/python -m src.cli.ingest >> /var/log/ingestion.log 2>&1
```

5. **Test Manually**

```bash
# Activate venv and test
source venv/bin/activate
python -m src.cli.ingest
```

### Pros
- ✅ Full control over environment
- ✅ No execution time limits
- ✅ Can run long-running processes
- ✅ Easy to debug and monitor

### Cons
- ⚠️ Requires server management
- ⚠️ Ongoing costs (even when idle)
- ⚠️ Need to handle updates/maintenance

---

## Option 4: Supabase Edge Functions (Requires Rewrite)

**Note**: Supabase Edge Functions use Deno/TypeScript, not Python. This would require rewriting the ingestion logic.

### If You Want to Explore This Option

1. Rewrite ingestion logic in TypeScript/Deno
2. Use Supabase's PostgreSQL client for Deno
3. Deploy as Edge Function
4. Schedule with Supabase Cron or external scheduler

**Not recommended** unless you want to rewrite the entire codebase.

---

## Option 5: Railway / Render / Fly.io (Platform-as-a-Service)

**Best for**: Simple deployment, managed infrastructure, minimal configuration

### Railway Example

1. **Connect Repository**

- Sign up at railway.app
- Connect GitHub repository
- Railway auto-detects Python project

2. **Configure Environment**

- Add `DATABASE_URL` environment variable (Supabase connection string)
- Add `LOG_FORMAT=json`
- Add `LOG_LEVEL=INFO`

3. **Set Up Cron Job**

Railway supports cron jobs via `railway.json`:

```json
{
  "cron": {
    "ingest": {
      "schedule": "0 2 * * *",
      "command": "python -m src.cli.ingest"
    }
  }
}
```

### Pros
- ✅ Simple deployment process
- ✅ Managed infrastructure
- ✅ Built-in cron support
- ✅ Automatic deployments from Git

### Cons
- ⚠️ Platform-specific (vendor lock-in)
- ⚠️ Monthly costs
- ⚠️ May have execution time limits

---

## Comparison Matrix

| Option | Cost | Complexity | Scheduling | Best For |
|--------|------|------------|------------|----------|
| **GitHub Actions** | Free (public) | Low | ✅ Built-in | Open source projects |
| **Cloud Functions** | Pay-per-use | Medium | ✅ Cloud Scheduler | Google Cloud users |
| **AWS Lambda** | Pay-per-use | Medium | ✅ EventBridge | AWS users |
| **Server/VM + Cron** | Fixed monthly | Medium | ✅ Cron | Full control needed |
| **Railway/Render** | Fixed monthly | Low | ✅ Built-in | Simple PaaS deployment |

---

## Recommended Approach

**For most users**: Start with **GitHub Actions** (Option 1)
- Free for public repositories
- Zero infrastructure management
- Easy to set up and test
- Built-in scheduling and logging

**If you need more control**: Use **Server/VM + Cron** (Option 3)
- Full control over environment
- No execution time limits
- Easy to debug and monitor

**If you're already in a cloud ecosystem**: Use **Cloud Functions/Lambda** (Option 2)
- Integrates with existing infrastructure
- Pay only for what you use
- Auto-scaling

---

## Next Steps

1. **Choose your deployment option**
2. **Set up Supabase database schema** (if not done):
   ```bash
   psql "[SUPABASE_CONNECTION_STRING]" -f scripts/setup_db.sql
   ```
3. **Test connection locally**:
   ```bash
   DATABASE_URL="[SUPABASE_CONNECTION_STRING]" python -m src.cli.ingest --dry-run
   ```
4. **Deploy using chosen method**
5. **Verify ingestion completes successfully**
6. **Set up monitoring/alerting** (optional)

---

## Security Notes

- **Never commit** `.env` files or connection strings to version control
- Use **secrets management** (GitHub Secrets, Cloud Secrets Manager, etc.)
- Use **SSL/TLS** for database connections (Supabase enforces this)
- Rotate database passwords regularly
- Restrict database access to known IPs if possible

---

## Troubleshooting

### Connection Issues

```bash
# Test Supabase connection
psql "[SUPABASE_CONNECTION_STRING]" -c "SELECT version();"

# Test from deployment environment
python -m src.cli.ingest --dry-run
```

### Timeout Issues

- Increase timeout settings (Cloud Functions: 540s max, Lambda: 900s max)
- Consider server/VM option if ingestion takes longer
- Optimize database queries if needed

### Dependency Issues

- Ensure Python 3.8+ is available
- Install system dependencies if needed (asyncpg may need `gcc` for compilation)
- Use virtual environments to isolate dependencies



