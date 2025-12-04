"""Environment configuration management."""

import os
from typing import Optional
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration from environment variables."""

    # Database configuration
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    DB_PASSWORD: Optional[str] = os.getenv("DB_PASSWORD")

    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")

    # Validation configuration
    MAX_DEPTH: int = int(os.getenv("MAX_DEPTH", "10"))

    @classmethod
    def validate(cls) -> None:
        """
        Validate required configuration.

        Raises:
            ValueError: If required configuration is missing
        """
        if not cls.DATABASE_URL:
            raise ValueError(
                "DATABASE_URL environment variable is required. "
                "Set it in .env file or environment."
            )

    @classmethod
    def get_database_url(cls) -> str:
        """
        Get database URL with password inserted if needed.

        Returns:
            Complete database URL

        Raises:
            ValueError: If DATABASE_URL is not set
        """
        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL is required")

        # If password is provided separately and not in URL, insert it
        if cls.DB_PASSWORD:
            # Check if password is already in the connection string
            # Format: postgresql://user:password@host or postgresql://user@host
            has_password_in_url = False
            if "@" in cls.DATABASE_URL:
                # Check if there's a colon before the @ (indicating password is present)
                user_part = cls.DATABASE_URL.split("@")[0]
                # Remove protocol prefix to check user:password part
                if "://" in user_part:
                    auth_part = user_part.split("://", 1)[1]
                    # If there's a colon in the auth part, password is already present
                    has_password_in_url = ":" in auth_part
            
            # Insert password into connection string if not present
            if not has_password_in_url and "@" in cls.DATABASE_URL:
                parts = cls.DATABASE_URL.split("@")
                if len(parts) == 2:
                    return f"{parts[0]}:{cls.DB_PASSWORD}@{parts[1]}"

        return cls.DATABASE_URL




