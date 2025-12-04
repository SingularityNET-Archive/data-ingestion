# Documentation Index

Welcome to the project documentation. This directory contains all project documentation organized by category.

## Documentation Structure

### Operations Documentation

Day-to-day operational procedures, troubleshooting, and production guides:

- **[Runbook](operations/runbook.md)** - Step-by-step operational procedures for running and maintaining the ingestion pipeline
- **[Production Checklist](operations/production-checklist.md)** - Pre-deployment verification checklist and environment configuration
- **[Troubleshooting Guide](operations/troubleshooting.md)** - Common issues and solutions
- **[Duplicate Diagnosis](operations/duplicate-diagnosis.md)** - Guide for detecting and resolving duplicate records

### Deployment Documentation

Setup guides and deployment options:

- **[Supabase Setup Guide](deployment/supabase-setup.md)** - Comprehensive step-by-step instructions for setting up Supabase and GitHub Actions
- **[Supabase Quick Start](deployment/supabase-quickstart.md)** - Quick reference checklist for rapid setup
- **[Deployment Options](deployment/deployment-options.md)** - Comprehensive guide covering all deployment methods (GitHub Actions, serverless, etc.)

### Archive

Historical and analysis files:

- **[Data Structure Analysis](archive/data-structure-analysis.json)** - Historical data structure analysis (for reference)

## Quick Navigation

### Getting Started
1. New to the project? Start with the [Supabase Quick Start](deployment/supabase-quickstart.md)
2. Need detailed setup? See the [Supabase Setup Guide](deployment/supabase-setup.md)
3. Ready to deploy? Review the [Production Checklist](operations/production-checklist.md)

### Operations
1. Running the pipeline? See the [Operations Runbook](operations/runbook.md)
2. Encountering issues? Check the [Troubleshooting Guide](operations/troubleshooting.md)
3. Need to verify data quality? See [Duplicate Diagnosis](operations/duplicate-diagnosis.md)

### Deployment
1. Choosing a deployment method? See [Deployment Options](deployment/deployment-options.md)
2. Setting up GitHub Actions? See [Supabase Setup Guide](deployment/supabase-setup.md)
3. Quick reference? See [Supabase Quick Start](deployment/supabase-quickstart.md)

## Technical Terms

Key terms used throughout the documentation:

- **Idempotent**: An operation that produces the same result regardless of how many times it is applied. The ingestion pipeline is idempotent - running it multiple times updates existing records without creating duplicates.

- **UPSERT**: A database operation that inserts a new record if it doesn't exist, or updates an existing record if it does. The pipeline uses UPSERT operations to handle duplicate prevention.

- **JSONB**: PostgreSQL's binary JSON format with indexing support. The pipeline stores flexible JSON data in JSONB columns for efficient querying.

- **Workgroup**: An organizational unit that groups related meetings together. Workgroups are processed first to ensure referential integrity.

- **Ingestion**: The process of importing external data (meeting summaries) into the system. The pipeline downloads JSON data from GitHub URLs and stores it in normalized database tables.

## Contributing

When adding or updating documentation:

1. Place files in the appropriate subdirectory (`operations/`, `deployment/`, or `archive/`)
2. Use kebab-case naming for files (e.g., `production-checklist.md`)
3. Update this index with links to new documentation
4. Update cross-references in related documentation files
5. Add entries to `CHANGELOG.md` for significant changes

## Related Documentation

- **Project README**: See the main [README.md](../README.md) for project overview and quick start
- **Specifications**: See `specs/` directory for feature specifications and implementation plans
- **Changelog**: See [CHANGELOG.md](../CHANGELOG.md) for version history and release notes



