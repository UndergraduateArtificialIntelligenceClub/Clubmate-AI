"""
Google Docs → RAG ingestion source.
Fetches a Google Doc by URL or ID, converts to plain text, and ingests into ChromaDB.
"""

import logging
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

logger = logging.getLogger(__name__)


def _extract_doc_id(url_or_id: str) -> str:
    if "docs.google.com" in url_or_id:
        parts = url_or_id.split("/d/")
        if len(parts) > 1:
            return parts[1].split("/")[0]
    return url_or_id


def _read_elements(elements) -> str:
    text = ""
    for el in elements:
        if "paragraph" in el:
            for pe in el["paragraph"].get("elements", []):
                if "textRun" in pe:
                    text += pe["textRun"].get("content", "")
        elif "table" in el:
            for row in el["table"].get("tableRows", []):
                for cell in row.get("tableCells", []):
                    text += _read_elements(cell.get("content", []))
    return text


def fetch_google_doc_text(url_or_id: str) -> tuple[str, str]:
    """
    Fetch a Google Doc and return (title, plain_text).
    Requires Google credentials configured via the dashboard.
    """
    from mcp_servers.google_auth import get_service

    doc_id = _extract_doc_id(url_or_id)
    service = get_service("docs", "v1")
    doc = service.documents().get(documentId=doc_id).execute()
    title = doc.get("title", "Untitled")
    text = _read_elements(doc.get("body", {}).get("content", []))
    return title, text.strip()


def ingest_google_doc(url_or_id: str) -> bool:
    """
    Fetch a Google Doc and ingest its content into the RAG vector store.
    Returns True on success.
    """
    from ragbot.rag import rag_ingest

    try:
        title, text = fetch_google_doc_text(url_or_id)
        if not text:
            logger.warning("Google Doc '%s' is empty — nothing to ingest", title)
            return False

        # Write to a temp file and ingest via the normal pipeline
        with tempfile.NamedTemporaryFile(
            suffix=".txt", mode="w", encoding="utf-8", delete=False
        ) as f:
            f.write(f"# {title}\n\n{text}")
            tmp_path = f.name

        result = rag_ingest(tmp_path)
        Path(tmp_path).unlink(missing_ok=True)
        logger.info("Ingested Google Doc '%s' (%d chars)", title, len(text))
        return result

    except Exception as e:
        logger.error("Failed to ingest Google Doc %s: %s", url_or_id, e)
        return False
