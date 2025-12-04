"""JSON downloader service using httpx async client."""

from typing import Any, Dict, List, Optional

import httpx

from src.lib.logger import get_logger

logger = get_logger(__name__)


class JSONDownloader:
    """Service for downloading JSON data from remote URLs."""

    def __init__(self, timeout: int = 30):
        """
        Initialize JSON downloader.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()

    async def download(self, url: str) -> List[Dict[str, Any]]:
        """
        Download JSON array from URL.

        Args:
            url: URL to download JSON from

        Returns:
            List of JSON objects (parsed from JSON array)

        Raises:
            httpx.HTTPError: If HTTP request fails
            ValueError: If response is not valid JSON or not an array
        """
        if not self.client:
            self.client = httpx.AsyncClient(timeout=self.timeout)

        logger.info(f"Downloading JSON from: {url}", extra={"source_url": url})

        try:
            response = await self.client.get(url)
            response.raise_for_status()

            # Parse JSON
            data = response.json()

            # Ensure it's a list
            if not isinstance(data, list):
                raise ValueError(f"Expected JSON array, got {type(data).__name__}")

            logger.info(
                f"Downloaded {len(data)} records from {url}",
                extra={"source_url": url, "record_count": len(data)},
            )

            return data

        except httpx.TimeoutException as e:
            logger.error(
                f"Connection timeout downloading from {url}: {e}",
                extra={"source_url": url, "error": str(e), "error_type": "timeout"},
            )
            raise
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error downloading from {url}: {e.response.status_code} {e.response.reason_phrase}",
                extra={
                    "source_url": url,
                    "error": str(e),
                    "error_type": "http_error",
                    "status_code": e.response.status_code,
                },
            )
            raise
        except httpx.RequestError as e:
            logger.error(
                f"Request error downloading from {url}: {e}",
                extra={"source_url": url, "error": str(e), "error_type": "request_error"},
            )
            raise
        except ValueError as e:
            logger.error(
                f"Invalid JSON format from {url}: {e}",
                extra={"source_url": url, "error": str(e), "error_type": "json_parse_error"},
            )
            raise

    async def download_multiple(self, urls: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Download JSON from multiple URLs.

        Args:
            urls: List of URLs to download from

        Returns:
            Dictionary mapping URL to downloaded JSON array

        Note:
            Failed downloads are logged but not included in result.
            Use this method to continue processing even if some sources fail.
        """
        results = {}

        for url in urls:
            try:
                data = await self.download(url)
                results[url] = data
            except Exception as e:
                logger.error(
                    f"Failed to download from {url}: {e}",
                    extra={"source_url": url, "error": str(e)},
                )
                # Continue with next URL
                continue

        return results




