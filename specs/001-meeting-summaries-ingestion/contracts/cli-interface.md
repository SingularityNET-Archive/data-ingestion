# CLI Interface Contract

**Date**: 2025-11-30  
**Feature**: 001-meeting-summaries-ingestion

## Overview

This document defines the command-line interface contract for the meeting summaries ingestion pipeline. The CLI uses Click for command definition and argument handling.

---

## Command Structure

### Main Command: `ingest`

Entry point for the ingestion pipeline.

```bash
python -m cli.ingest [OPTIONS] [URLS...]
```

### Positional Arguments

- `URLS` (optional): One or more JSON source URLs. If not provided, uses default URLs from configuration.

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--database-url` | `-d` | String | `$DATABASE_URL` | PostgreSQL connection string |
| `--db-password` | `-p` | String | `$DB_PASSWORD` | Database password (if not in URL) |
| `--dry-run` | | Flag | `False` | Validate and parse data without inserting to database |
| `--verbose` | `-v` | Flag | `False` | Enable verbose logging |
| `--log-format` | | Choice | `json` | Log format: `json` or `text` |
| `--max-depth` | | Integer | `10` | Maximum nesting depth for JSON validation |
| `--skip-validation` | | Flag | `False` | Skip JSON structure validation (not recommended) |
| `--help` | `-h` | Flag | | Show help message |

---

## Command Examples

### Basic Usage

```bash
# Use default URLs from environment/config
python -m cli.ingest

# Specify custom URLs
python -m cli.ingest \
  https://raw.githubusercontent.com/.../2025/meeting-summaries-array.json \
  https://raw.githubusercontent.com/.../2024/meeting-summaries-array.json

# Dry run (validate without inserting)
python -m cli.ingest --dry-run

# Verbose logging
python -m cli.ingest --verbose

# Custom database connection
python -m cli.ingest \
  --database-url "postgresql://user:pass@localhost:5432/dbname"
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes* | PostgreSQL connection string (format: `postgresql://user:password@host:port/database`) |
| `DB_PASSWORD` | No | Database password (if not included in DATABASE_URL) |
| `LOG_LEVEL` | No | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: `INFO`) |
| `LOG_FORMAT` | No | Log format: `json` or `text` (default: `json`) |

*Required unless provided via `--database-url` option

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success - all sources processed successfully |
| `1` | General error - see error message |
| `2` | Configuration error - invalid database URL or missing credentials |
| `3` | Validation error - JSON structure incompatible or validation failures |
| `4` | Network error - failed to download JSON sources |
| `5` | Database error - connection failure or transaction errors |

---

## Output Format

### Success Output

```json
{
  "timestamp": "2025-11-30T12:00:00Z",
  "level": "INFO",
  "event": "ingestion_complete",
  "sources_processed": 4,
  "records_inserted": 677,
  "records_updated": 0,
  "records_skipped": 0,
  "duration_seconds": 45.2
}
```

### Error Output

```json
{
  "timestamp": "2025-11-30T12:00:00Z",
  "level": "ERROR",
  "event": "ingestion_failed",
  "source_url": "https://...",
  "error": "Network error: Connection timeout",
  "sources_processed": 2,
  "sources_failed": 1,
  "records_inserted": 300
}
```

### Progress Output (verbose mode)

```json
{
  "timestamp": "2025-11-30T12:00:00Z",
  "level": "INFO",
  "event": "source_processing",
  "source_url": "https://...",
  "status": "downloading"
}
```

```json
{
  "timestamp": "2025-11-30T12:00:01Z",
  "level": "INFO",
  "event": "source_processing",
  "source_url": "https://...",
  "status": "validating",
  "record_count": 122
}
```

```json
{
  "timestamp": "2025-11-30T12:00:02Z",
  "level": "INFO",
  "event": "source_processing",
  "source_url": "https://...",
  "status": "ingesting",
  "records_processed": 50,
  "total_records": 122
}
```

---

## Click Command Definition

```python
import click
from typing import List, Optional

@click.command()
@click.argument('urls', nargs=-1, required=False)
@click.option('--database-url', '-d', 
              default=None,
              envvar='DATABASE_URL',
              help='PostgreSQL connection string')
@click.option('--db-password', '-p',
              default=None,
              envvar='DB_PASSWORD',
              help='Database password (if not in URL)')
@click.option('--dry-run', is_flag=True,
              help='Validate and parse data without inserting to database')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose logging')
@click.option('--log-format',
              type=click.Choice(['json', 'text'], case_sensitive=False),
              default='json',
              envvar='LOG_FORMAT',
              help='Log format: json or text')
@click.option('--max-depth', type=int, default=10,
              help='Maximum nesting depth for JSON validation')
@click.option('--skip-validation', is_flag=True,
              help='Skip JSON structure validation (not recommended)')
def ingest(urls: tuple, database_url: Optional[str], db_password: Optional[str],
           dry_run: bool, verbose: bool, log_format: str, 
           max_depth: int, skip_validation: bool):
    """
    Ingest meeting summaries from JSON sources into PostgreSQL database.
    
    URLS: One or more JSON source URLs. If not provided, uses default URLs.
    """
    # Implementation
    pass
```

---

## Configuration File Support (Optional)

Future enhancement: Support for configuration file (YAML/JSON) for default URLs and settings.

```yaml
# config.yaml
sources:
  - url: https://raw.githubusercontent.com/.../2025/meeting-summaries-array.json
    year: 2025
  - url: https://raw.githubusercontent.com/.../2024/meeting-summaries-array.json
    year: 2024
  - url: https://raw.githubusercontent.com/.../2023/meeting-summaries-array.json
    year: 2023
  - url: https://raw.githubusercontent.com/.../2022/meeting-summaries-array.json
    year: 2022

database:
  url: ${DATABASE_URL}
  password: ${DB_PASSWORD}

logging:
  level: INFO
  format: json
```

---

## Error Handling Contract

### Network Errors
- **Connection timeout**: Log error, continue with next source (if multiple)
- **HTTP error (4xx/5xx)**: Log error with status code, continue with next source
- **Invalid URL**: Log error, skip source, continue

### Validation Errors
- **Structure incompatibility**: Log error, skip source, continue with next source
- **Record validation failure**: Log error with record details, skip record, continue processing

### Database Errors
- **Connection failure**: Log error, exit with code 5
- **Transaction failure**: Log error with transaction details, rollback, continue with next record
- **Constraint violation**: Log conflict details, handle via UPSERT, continue

---

## Performance Expectations

- **Download time**: < 5 seconds per source (depends on network)
- **Validation time**: < 1 second per 100 records
- **Ingestion time**: < 10 minutes for all sources (677 records total)
- **Memory usage**: Process records in batches to avoid loading entire dataset in memory

---

## Testing Interface

For testing purposes, the CLI should support:

```bash
# Test with sample data
python -m cli.ingest --dry-run sample-data.json

# Test database connection
python -m cli.ingest --dry-run --database-url "postgresql://..."
```




