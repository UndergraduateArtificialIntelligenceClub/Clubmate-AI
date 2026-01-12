"""
Files Router
============
API endpoints for file management.

Endpoints:
- GET /files/ - List all files
- POST /files/upload - Upload a new file
- GET /files/{id}/download - Download a file
- DELETE /files/{id} - Delete a file
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.file import FileResponse as FileSchema
from app.services.file_service import FileService


router = APIRouter()


@router.get("/", response_model=List[FileSchema])
async def list_files(
    session: AsyncSession = Depends(get_session),
):
    """
    List all uploaded files.
    
    Returns file metadata (not the actual file content).
    """
    files, total = await FileService.get_all(session)
    return files


@router.post("/upload", response_model=FileSchema, status_code=201)
async def upload_file(
    file: UploadFile = FastAPIFile(..., description="File to upload"),
    session: AsyncSession = Depends(get_session),
):
    """
    Upload a new file.
    
    Accepts multipart/form-data with a 'file' field.
    Allowed file types: pdf, doc, docx, xls, xlsx, csv, txt, png, jpg, jpeg, gif
    Maximum size: 50MB
    """
    try:
        db_file = await FileService.upload(session, file)
        return db_file
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Download a file by ID.
    
    Returns the actual file content with appropriate Content-Disposition header.
    """
    file = await FileService.get_by_id(session, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = FileService.get_file_path(file)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=file_path,
        filename=file.filename,
        media_type=file.mime_type,
    )


@router.get("/{file_id}", response_model=FileSchema)
async def get_file(
    file_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get file metadata by ID (not the actual file content)."""
    file = await FileService.get_by_id(session, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@router.delete("/{file_id}", status_code=204)
async def delete_file(
    file_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Delete a file by ID (removes from both database and filesystem)."""
    deleted = await FileService.delete(session, file_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="File not found")
    return None
