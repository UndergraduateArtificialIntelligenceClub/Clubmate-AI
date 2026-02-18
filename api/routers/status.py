"""
Status endpoints — bot health, connected servers, RAG doc count.
"""

import sys
import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from api.auth import verify_discord_admin
from config import settings

router = APIRouter(prefix="/status", tags=["status"])


@router.get("")
async def get_status(_user: dict = Depends(verify_discord_admin)):
    """Return health status of all components."""
    from ragbot import rag_has_documents, rag_chunk_count

    rag_status = "unavailable"
    doc_count = 0
    try:
        has_docs = await asyncio.to_thread(rag_has_documents)
        rag_status = "ready"
        doc_count = await asyncio.to_thread(rag_chunk_count) if has_docs else 0
    except Exception:
        pass

    google_connected = Path(settings.google_token_path).exists()

    return {
        "bot": "online",
        "rag": {
            "status": rag_status,
            "document_chunks": doc_count,
        },
        "google_connected": google_connected,
        "model": settings.default_llm_model,
        "exec_role": settings.exec_role_name,
    }
