"""Export manager for handling async exports and download links.

This module provides functionality for managing large exports (>10k rows)
asynchronously, generating download links, and tracking export job status.
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from enum import Enum
import json
import csv
import io
from pathlib import Path


class ExportStatus(str, Enum):
    """Export job status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class ExportJob:
    """Represents an async export job."""
    
    def __init__(
        self,
        job_id: str,
        user_id: str,
        format: str,
        filters: Dict[str, Any],
        created_at: datetime,
        status: ExportStatus = ExportStatus.PENDING,
        file_path: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        self.job_id = job_id
        self.user_id = user_id
        self.format = format
        self.filters = filters
        self.created_at = created_at
        self.status = status
        self.file_path = file_path
        self.error_message = error_message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert export job to dictionary."""
        return {
            "job_id": self.job_id,
            "user_id": self.user_id,
            "format": self.format,
            "filters": self.filters,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "file_path": self.file_path,
            "error_message": self.error_message,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExportJob":
        """Create export job from dictionary."""
        return cls(
            job_id=data["job_id"],
            user_id=data["user_id"],
            format=data["format"],
            filters=data["filters"],
            created_at=datetime.fromisoformat(data["created_at"]),
            status=ExportStatus(data["status"]),
            file_path=data.get("file_path"),
            error_message=data.get("error_message"),
        )


class ExportManager:
    """Manages async export jobs and file storage.
    
    This is a simplified in-memory implementation. For production,
    consider using:
    - Redis for job storage
    - S3/Cloud Storage for file storage
    - Celery or similar for async task processing
    """
    
    def __init__(self, storage_dir: Optional[Path] = None, job_ttl_hours: int = 24):
        """Initialize export manager.
        
        Args:
            storage_dir: Directory to store export files (default: ./exports)
            job_ttl_hours: Time-to-live for export jobs in hours (default: 24)
        """
        self.storage_dir = storage_dir or Path("./exports")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.job_ttl_hours = job_ttl_hours
        
        # In-memory job storage (use Redis/DB in production)
        self._jobs: Dict[str, ExportJob] = {}
    
    def create_job(
        self,
        user_id: str,
        format: str,
        filters: Dict[str, Any],
    ) -> ExportJob:
        """Create a new export job.
        
        Args:
            user_id: ID of user requesting export
            format: Export format ('csv' or 'json')
            filters: Filter parameters for the export
            
        Returns:
            Created export job
        """
        job_id = str(uuid.uuid4())
        job = ExportJob(
            job_id=job_id,
            user_id=user_id,
            format=format,
            filters=filters,
            created_at=datetime.utcnow(),
            status=ExportStatus.PENDING,
        )
        self._jobs[job_id] = job
        return job
    
    def get_job(self, job_id: str) -> Optional[ExportJob]:
        """Get export job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            Export job or None if not found
        """
        job = self._jobs.get(job_id)
        if job:
            # Check if job has expired
            age = datetime.utcnow() - job.created_at
            if age > timedelta(hours=self.job_ttl_hours):
                job.status = ExportStatus.EXPIRED
        return job
    
    def update_job_status(
        self,
        job_id: str,
        status: ExportStatus,
        file_path: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """Update export job status.
        
        Args:
            job_id: Job ID
            status: New status
            file_path: Path to exported file (if completed)
            error_message: Error message (if failed)
            
        Returns:
            True if job was updated, False if not found
        """
        job = self._jobs.get(job_id)
        if not job:
            return False
        
        job.status = status
        if file_path:
            job.file_path = file_path
        if error_message:
            job.error_message = error_message
        
        return True
    
    def save_export_file(
        self,
        job_id: str,
        content: bytes,
        format: str,
    ) -> str:
        """Save export file to disk.
        
        Args:
            job_id: Job ID
            content: File content as bytes
            format: File format ('csv' or 'json')
            
        Returns:
            Path to saved file
        """
        filename = f"{job_id}.{format}"
        file_path = self.storage_dir / filename
        file_path.write_bytes(content)
        return str(file_path)
    
    def get_export_file(self, job_id: str) -> Optional[bytes]:
        """Get export file content.
        
        Args:
            job_id: Job ID
            
        Returns:
            File content as bytes, or None if not found
        """
        job = self.get_job(job_id)
        if not job or not job.file_path:
            return None
        
        file_path = Path(job.file_path)
        if not file_path.exists():
            return None
        
        return file_path.read_bytes()
    
    def cleanup_expired_jobs(self) -> int:
        """Clean up expired export jobs and files.
        
        Returns:
            Number of jobs cleaned up
        """
        now = datetime.utcnow()
        expired_jobs = []
        
        for job_id, job in self._jobs.items():
            age = now - job.created_at
            if age > timedelta(hours=self.job_ttl_hours):
                expired_jobs.append(job_id)
        
        for job_id in expired_jobs:
            job = self._jobs.pop(job_id, None)
            if job and job.file_path:
                try:
                    Path(job.file_path).unlink(missing_ok=True)
                except Exception:
                    pass  # Ignore cleanup errors
        
        return len(expired_jobs)
    
    def list_user_jobs(self, user_id: str) -> list[ExportJob]:
        """List export jobs for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of export jobs
        """
        return [
            job for job in self._jobs.values()
            if job.user_id == user_id
        ]


# Global export manager instance (singleton)
_export_manager: Optional[ExportManager] = None


def get_export_manager() -> ExportManager:
    """Get global export manager instance."""
    global _export_manager
    if _export_manager is None:
        _export_manager = ExportManager()
    return _export_manager


def reset_export_manager():
    """Reset export manager (useful for testing)."""
    global _export_manager
    _export_manager = None

