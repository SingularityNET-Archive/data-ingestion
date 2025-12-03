"""CLI command for ingesting meeting summaries."""

import asyncio
from typing import List, Optional

import click

from src.db.connection import get_db_connection
from src.lib.config import Config
from src.lib.logger import setup_logger
from src.services.ingestion_service import IngestionService
from src.services.json_downloader import JSONDownloader
from src.services.json_validator import JSONValidator

# Default URLs from specification
DEFAULT_URLS = [
    "https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2025/meeting-summaries-array.json",
    "https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2024/meeting-summaries-array.json",
    "https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2023/meeting-summaries-array.json",
    "https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2022/meeting-summaries-array.json",
]


@click.command()
@click.argument("urls", nargs=-1, required=False)
@click.option(
    "--database-url",
    "-d",
    default=None,
    envvar="DATABASE_URL",
    help="PostgreSQL connection string",
)
@click.option(
    "--db-password",
    "-p",
    default=None,
    envvar="DB_PASSWORD",
    help="Database password (if not in URL)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Validate and parse data without inserting to database",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
@click.option(
    "--log-format",
    type=click.Choice(["json", "text"], case_sensitive=False),
    default=None,
    envvar="LOG_FORMAT",
    help="Log format: json or text",
)
@click.option(
    "--max-depth",
    type=int,
    default=10,
    help="Maximum nesting depth for JSON validation",
)
@click.option(
    "--skip-validation",
    is_flag=True,
    help="Skip JSON structure validation (not recommended)",
)
def ingest(
    urls: tuple,
    database_url: Optional[str],
    db_password: Optional[str],
    dry_run: bool,
    verbose: bool,
    log_format: Optional[str],
    max_depth: int,
    skip_validation: bool,
):
    """
    Ingest meeting summaries from JSON sources into PostgreSQL database.

    URLS: One or more JSON source URLs. If not provided, uses default URLs.
    """
    # Setup logging
    log_level = "DEBUG" if verbose else Config.LOG_LEVEL
    log_format_value = log_format or Config.LOG_FORMAT
    logger = setup_logger(level=log_level, log_format=log_format_value)

    logger.info("Starting meeting summaries ingestion", extra={"event": "ingestion_start"})

    # Determine URLs to process
    urls_to_process = list(urls) if urls else DEFAULT_URLS

    if not urls_to_process:
        logger.error("No URLs provided and no default URLs configured")
        click.echo("Error: No URLs provided", err=True)
        raise click.Abort()

    logger.info(
        f"Processing {len(urls_to_process)} source(s)",
        extra={"event": "sources_identified", "source_count": len(urls_to_process)},
    )

    # Get database URL
    db_url = None
    if not dry_run:
        try:
            db_url = database_url or Config.get_database_url()
        except Exception as e:
            logger.error(f"Failed to get database URL: {e}", extra={"error": str(e)})
            click.echo(f"Error: Database configuration failed: {e}", err=True)
            raise click.Abort()

    # Run async ingestion
    try:
        asyncio.run(
            _run_ingestion(
                urls_to_process,
                db_url,
                dry_run,
                skip_validation,
                logger,
            )
        )
    except KeyboardInterrupt:
        logger.warning("Ingestion interrupted by user")
        click.echo("\nIngestion interrupted", err=True)
        raise click.Abort()
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", extra={"error": str(e)})
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


async def _run_ingestion(
    urls: List[str],
    db_url: Optional[str],
    dry_run: bool,
    skip_validation: bool,
    logger,
):
    """Run the ingestion process."""
    validator = JSONValidator()
    ingestion_service = None
    db_connection = None

    # Setup database connection if not dry-run
    if not dry_run and db_url:
        try:
            db_connection = get_db_connection(db_url)
            await db_connection.create_pool()
            logger.info("Database connection established")
            ingestion_service = IngestionService(db_connection)
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}", extra={"error": str(e)})
            raise

    total_stats = {
        "sources_processed": 0,
        "sources_failed": 0,
        "records_inserted": 0,
        "records_updated": 0,
        "records_skipped": 0,
    }

    async with JSONDownloader() as downloader:
        for url in urls:
            try:
                logger.info(
                    f"Processing source: {url}", extra={"source_url": url, "status": "downloading"}
                )

                # Download JSON
                json_data = await downloader.download(url)

                logger.info(
                    f"Downloaded {len(json_data)} records from {url}",
                    extra={
                        "source_url": url,
                        "status": "validating",
                        "record_count": len(json_data),
                    },
                )

                # Validate structure compatibility
                if not skip_validation:
                    if not validator.validate_structure(json_data, url):
                        logger.error(
                            f"Structure validation failed for {url}",
                            extra={
                                "source_url": url,
                                "error_type": "validation_error",
                                "event": "structure_validation_failed",
                            },
                        )
                        total_stats["sources_failed"] += 1
                        continue

                # Validate records
                valid_records, invalid_records = validator.validate_records(json_data, url)
                total_stats["records_skipped"] += len(invalid_records)

                logger.info(
                    f"Validated records from {url}: {len(valid_records)} valid, {len(invalid_records)} invalid",
                    extra={
                        "source_url": url,
                        "status": "ingesting",
                        "records_processed": len(valid_records),
                        "total_records": len(json_data),
                    },
                )

                # Ingest records
                if ingestion_service and valid_records:
                    stats = await ingestion_service.process_meetings(
                        valid_records, url, dry_run, original_json_records=json_data
                    )
                    total_stats["records_inserted"] += stats["succeeded"]
                    total_stats["sources_processed"] += 1
                elif dry_run:
                    # In dry-run mode, just count valid records
                    total_stats["records_inserted"] += len(valid_records)
                    total_stats["sources_processed"] += 1

            except Exception as e:
                # Determine error type
                error_type = type(e).__name__
                logger.error(
                    f"Failed to process source {url}: {e}",
                    extra={
                        "source_url": url,
                        "error": str(e),
                        "error_type": error_type,
                        "event": "source_processing_failed",
                    },
                )
                total_stats["sources_failed"] += 1
                continue

    # Log completion
    logger.info(
        "Ingestion completed",
        extra={
            "event": "ingestion_complete",
            "sources_processed": total_stats["sources_processed"],
            "sources_failed": total_stats["sources_failed"],
            "records_inserted": total_stats["records_inserted"],
            "records_skipped": total_stats["records_skipped"],
        },
    )

    # Close database connection
    if db_connection:
        await db_connection.close_pool()


if __name__ == "__main__":
    """
    CLI entry point for meeting summaries ingestion.

    Usage examples:
        # Basic usage with default URLs
        python -m src.cli.ingest

        # Specify custom URLs
        python -m src.cli.ingest https://example.com/data1.json https://example.com/data2.json

        # Dry run (validate without inserting)
        python -m src.cli.ingest --dry-run

        # Verbose logging
        python -m src.cli.ingest --verbose

        # Custom database connection
        python -m src.cli.ingest --database-url "postgresql://user:pass@localhost:5432/dbname"

    Environment variables:
        DATABASE_URL: PostgreSQL connection string (required unless --database-url provided)
        DB_PASSWORD: Database password (if not in DATABASE_URL)
        LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, default: INFO)
        LOG_FORMAT: Log format (json or text, default: json)
    """
    ingest()
