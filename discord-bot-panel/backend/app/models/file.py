"""
File Model
==========
Metadata for uploaded files (PDFs, Excel, etc.).

The actual file content is stored on the filesystem.
This table stores metadata and the storage path.

Why filesystem storage instead of database BLOBs?
- Better performance for large files
- Easier to migrate to S3/cloud storage later
- Database backups stay small
- Can serve files directly via web server
"""

from typing import Optional
from sqlmodel import Field

from app.models.base import BaseModel, TimestampMixin


class File(BaseModel, TimestampMixin, table=True):
    """
    Uploaded file metadata.
    
    File content is stored at storage_path on the filesystem.
    This record tracks metadata for listing and management.
    """
    __tablename__ = "files"
    
    # Original filename (for display)
    filename: str = Field(
        max_length=255,
        description="Original filename as uploaded"
    )
    
    # Storage path (relative to uploads directory)
    # Example: "2024/01/abc123_document.pdf"
    storage_path: str = Field(
        max_length=512,
        unique=True,
        description="Path on filesystem relative to upload directory"
    )
    
    # File metadata
    mime_type: str = Field(
        max_length=128,
        description="MIME type (e.g., 'application/pdf')"
    )
    file_size_bytes: int = Field(
        description="File size in bytes"
    )
    
    # Optional description
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional file description"
    )
    
    # Audit trail
    uploaded_by: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
        index=True,
        description="User who uploaded the file"
    )
