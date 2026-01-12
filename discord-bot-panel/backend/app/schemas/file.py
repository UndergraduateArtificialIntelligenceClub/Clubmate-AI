"""
File Schemas
============
Response schemas for file operations.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class FileResponse(BaseModel):
    """Schema for file in API responses."""
    id: int
    filename: str
    mime_type: str
    file_size_bytes: int
    description: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    """List of files."""
    items: List[FileResponse]
    total: int
