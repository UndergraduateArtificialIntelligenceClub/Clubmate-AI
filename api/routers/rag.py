"""
RAG management endpoints — ingest docs, reset DB, check status.
"""

import sys
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from api.auth import verify_discord_admin

router = APIRouter(prefix="/rag", tags=["rag"])


class GoogleDocIngest(BaseModel):
    url: str  # Google Doc URL


@router.get("/status")
async def rag_status(_user: dict = Depends(verify_discord_admin)):
    """Check RAG status and document count."""
    try:
        from ragbot import rag_has_documents
        from ragbot.rag import _get_rag

        has_docs = rag_has_documents()
        rag = _get_rag()
        count = rag.vector_store._collection.count()
        return {"status": "ready", "has_documents": has_docs, "chunk_count": count}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/ingest/file")
async def ingest_file(
    file: UploadFile = File(...),
    _user: dict = Depends(verify_discord_admin),
):
    """Upload and ingest a file (.pdf, .txt, .md) into the knowledge base."""
    from ragbot.sources.file_upload import ingest_uploaded_file

    filename = file.filename or "upload"
    content = await file.read()

    try:
        success = ingest_uploaded_file(filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

    if not success:
        raise HTTPException(status_code=422, detail="File was processed but no content was extracted")

    return {"message": f"'{filename}' ingested successfully into the knowledge base."}


@router.post("/ingest/google-doc")
async def ingest_google_doc(
    body: GoogleDocIngest,
    _user: dict = Depends(verify_discord_admin),
):
    """Fetch a Google Doc by URL and ingest it into the knowledge base."""
    from ragbot.sources.google_docs import ingest_google_doc as _ingest

    try:
        success = _ingest(body.url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest Google Doc: {e}")

    if not success:
        raise HTTPException(status_code=422, detail="Google Doc was fetched but no content was extracted")

    return {"message": "Google Doc ingested successfully into the knowledge base."}


@router.delete("/reset")
async def reset_rag(_user: dict = Depends(verify_discord_admin)):
    """Clear all documents from the RAG knowledge base. Cannot be undone."""
    from ragbot import db_reset

    success = db_reset()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to reset knowledge base")
    return {"message": "Knowledge base cleared successfully."}
