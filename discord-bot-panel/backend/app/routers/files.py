from fastapi import APIRouter, Depends, UploadFile, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
import os
import shutil
from app.db.session import get_session
from app.models.file import FileRecord
from app.auth.dependencies import get_current_admin

router = APIRouter(prefix="/files", tags=["Files"])
UPLOAD_DIR = "../storage/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/")
async def list_files(
    session: AsyncSession = Depends(get_session), user=Depends(get_current_admin)
):
    stmt = select(FileRecord).order_by(FileRecord.created_at.desc())
    res = await session.execute(stmt)
    return res.scalars().all()


@router.post("/upload")
async def upload_file(
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_admin),
):
    # Create folder with the exact name of the file (minus extension) or full name? 
    # User said "folder with the same exact name". Let's assume filename.
    # If filename is "bot.py", folder is "storage/uploads/bot.py/" and file is "storage/uploads/bot.py/bot.py"
    # This ensures uniqueness and grouping if they add more related files later?
    # Or maybe they meant "storage/uploads/bot/" for "bot.py"?
    # I'll use the full filename for the folder to be safe and "exact".
    
    file_folder = os.path.join(UPLOAD_DIR, file.filename)
    os.makedirs(file_folder, exist_ok=True)
    
    file_path = os.path.join(file_folder, file.filename)

    # Save to disk
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")

    # Save DB record
    record = FileRecord(
        filename=file.filename,
        file_size_bytes=os.path.getsize(file_path),
        mime_type=file.content_type or "application/octet-stream",
        local_path=file_path,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_admin),
):
    file_record = await session.get(FileRecord, file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    # Remove from disk
    if os.path.exists(file_record.local_path):
        os.remove(file_record.local_path)

    # Remove from DB
    await session.delete(file_record)
    await session.commit()
    return {"status": "deleted", "id": file_id}
