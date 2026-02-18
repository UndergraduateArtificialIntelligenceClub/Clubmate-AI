"""
File upload → RAG ingestion source.
Receives file bytes from the FastAPI backend and ingests into ChromaDB.
Supports .pdf, .txt, .md
"""

import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown"}


def ingest_uploaded_file(filename: str, file_bytes: bytes) -> bool:
    """
    Write file_bytes to a temp file and ingest into the RAG vector store.
    Returns True on success.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from ragbot.rag import rag_ingest

    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {suffix}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(file_bytes)
        tmp_path = f.name

    try:
        result = rag_ingest(tmp_path)
        logger.info("Ingested uploaded file: %s (%d bytes)", filename, len(file_bytes))
        return result
    finally:
        Path(tmp_path).unlink(missing_ok=True)
