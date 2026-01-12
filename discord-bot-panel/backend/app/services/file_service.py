"""
File Service
============
Business logic for file storage and management.

File storage strategy:
- Files stored on local filesystem in uploads/ directory
- Organized by year/month subdirectories
- Unique filename prefix to prevent collisions
- Metadata stored in PostgreSQL for queries
"""

import os
import uuid
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.config import get_settings
from app.models import File, ActivityLog

settings = get_settings()


class FileService:
    """
    Service for file upload, download, and management.
    """
    
    @staticmethod
    def _get_storage_path(filename: str) -> tuple[str, Path]:
        """
        Generate a unique storage path for a file.
        
        Returns:
            Tuple of (relative path for DB, absolute path for filesystem)
        """
        # Organize files by year/month
        now = datetime.now(timezone.utc)
        subdir = f"{now.year}/{now.month:02d}"
        
        # Add UUID prefix to prevent filename collisions
        safe_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
        
        # Relative path for database
        relative_path = f"{subdir}/{safe_filename}"
        
        # Absolute path for filesystem
        abs_path = settings.upload_path / relative_path
        
        # Ensure parent directory exists
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        
        return relative_path, abs_path
    
    @staticmethod
    def _validate_file(file: UploadFile) -> None:
        """
        Validate file before upload.
        
        Raises ValueError if validation fails.
        """
        if not file.filename:
            raise ValueError("Filename is required")
        
        # Check extension
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in settings.allowed_extension_list:
            raise ValueError(f"File type '{ext}' not allowed. Allowed: {settings.allowed_extensions}")
        
        # Note: Size is checked during upload by reading chunks
    
    @staticmethod
    async def upload(
        session: AsyncSession,
        file: UploadFile,
        user_id: Optional[int] = None,
        description: Optional[str] = None,
    ) -> File:
        """
        Upload a file and create database record.
        
        The file is saved to disk and metadata is stored in the database.
        """
        # Validate file
        FileService._validate_file(file)
        
        # Generate storage path
        relative_path, abs_path = FileService._get_storage_path(file.filename)
        
        # Determine MIME type
        mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
        
        # Save file to disk (chunked for memory efficiency)
        file_size = 0
        with open(abs_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                file_size += len(chunk)
                
                # Check size limit
                if file_size > settings.max_file_size:
                    # Clean up partial file
                    os.remove(abs_path)
                    raise ValueError(f"File too large. Maximum size: {settings.max_file_size / 1024 / 1024}MB")
                
                f.write(chunk)
        
        # Create database record
        db_file = File(
            filename=file.filename,
            storage_path=relative_path,
            mime_type=mime_type,
            file_size_bytes=file_size,
            description=description,
            uploaded_by=user_id,
        )
        
        session.add(db_file)
        await session.commit()
        await session.refresh(db_file)
        
        # Log the action
        log = ActivityLog(
            user_id=user_id,
            action="upload_file",
            details={"file_id": db_file.id, "filename": file.filename, "size": file_size},
            status="success",
        )
        session.add(log)
        await session.commit()
        
        return db_file
    
    @staticmethod
    async def get_all(session: AsyncSession) -> tuple[List[File], int]:
        """Get all files with total count."""
        count_query = select(func.count()).select_from(File)
        total = (await session.execute(count_query)).scalar() or 0
        
        query = select(File).order_by(File.created_at.desc())
        result = await session.execute(query)
        files = result.scalars().all()
        
        return list(files), total
    
    @staticmethod
    async def get_by_id(session: AsyncSession, file_id: int) -> Optional[File]:
        """Get a single file by ID."""
        query = select(File).where(File.id == file_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    def get_file_path(file: File) -> Path:
        """Get the absolute filesystem path for a file."""
        return settings.upload_path / file.storage_path
    
    @staticmethod
    async def delete(
        session: AsyncSession,
        file_id: int,
        user_id: Optional[int] = None,
    ) -> bool:
        """
        Delete a file from database and filesystem.
        
        Returns True if deleted, False if not found.
        """
        file = await FileService.get_by_id(session, file_id)
        if not file:
            return False
        
        # Get file path before deleting record
        file_path = FileService.get_file_path(file)
        filename = file.filename
        
        # Delete from database
        await session.delete(file)
        await session.commit()
        
        # Delete from filesystem (if exists)
        try:
            if file_path.exists():
                os.remove(file_path)
        except OSError as e:
            # Log but don't fail - DB record is already deleted
            print(f"Warning: Could not delete file {file_path}: {e}")
        
        # Log the action
        log = ActivityLog(
            user_id=user_id,
            action="delete_file",
            details={"file_id": file_id, "filename": filename},
            status="success",
        )
        session.add(log)
        await session.commit()
        
        return True
