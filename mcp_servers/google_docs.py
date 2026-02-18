"""
Google Docs MCP Server for Clubmate AI.
Provides tools to read, create, and append content to Google Docs.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mcp_servers.google_auth import get_service

logger = logging.getLogger(__name__)
mcp = FastMCP("Google Docs")


def _extract_doc_id(doc_url_or_id: str) -> str:
    """Extract document ID from a Google Docs URL or return as-is if already an ID."""
    if "docs.google.com" in doc_url_or_id:
        # URL format: https://docs.google.com/document/d/DOC_ID/edit
        parts = doc_url_or_id.split("/d/")
        if len(parts) > 1:
            return parts[1].split("/")[0]
    return doc_url_or_id


def _read_structural_elements(elements) -> str:
    """Recursively extract plain text from Google Docs structural elements."""
    text = ""
    for element in elements:
        if "paragraph" in element:
            for pe in element["paragraph"].get("elements", []):
                if "textRun" in pe:
                    text += pe["textRun"].get("content", "")
        elif "table" in element:
            for row in element["table"].get("tableRows", []):
                for cell in row.get("tableCells", []):
                    text += _read_structural_elements(cell.get("content", []))
        elif "tableOfContents" in element:
            text += _read_structural_elements(
                element["tableOfContents"].get("content", [])
            )
    return text


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def read_document(doc_url_or_id: str) -> dict:
    """
    Read the full text content of a Google Document.

    Args:
        doc_url_or_id: Google Doc URL or document ID
    """
    doc_id = _extract_doc_id(doc_url_or_id)
    service = get_service("docs", "v1")
    doc = service.documents().get(documentId=doc_id).execute()
    title = doc.get("title", "Untitled")
    content = _read_structural_elements(doc.get("body", {}).get("content", []))
    return {
        "title": title,
        "document_id": doc_id,
        "content": content.strip(),
        "url": f"https://docs.google.com/document/d/{doc_id}/edit",
    }


@mcp.tool()
def create_document(title: str, content: Optional[str] = None) -> dict:
    """
    Create a new Google Document.

    Args:
        title: Title of the new document
        content: Initial text content to insert (optional)
    """
    service = get_service("docs", "v1")
    doc = service.documents().create(body={"title": title}).execute()
    doc_id = doc.get("documentId")

    if content:
        service.documents().batchUpdate(
            documentId=doc_id,
            body={
                "requests": [
                    {
                        "insertText": {
                            "location": {"index": 1},
                            "text": content,
                        }
                    }
                ]
            },
        ).execute()

    url = f"https://docs.google.com/document/d/{doc_id}/edit"
    logger.info("Created document: %s (%s)", title, doc_id)
    return {
        "document_id": doc_id,
        "title": title,
        "url": url,
        "message": f"Document '{title}' created. {url}",
    }


@mcp.tool()
def append_to_document(doc_url_or_id: str, text: str) -> dict:
    """
    Append text to the end of an existing Google Document.

    Args:
        doc_url_or_id: Google Doc URL or document ID
        text: Text to append
    """
    doc_id = _extract_doc_id(doc_url_or_id)
    service = get_service("docs", "v1")

    # Get current document to find the end index
    doc = service.documents().get(documentId=doc_id).execute()
    content = doc.get("body", {}).get("content", [])
    end_index = content[-1].get("endIndex", 1) - 1 if content else 1

    service.documents().batchUpdate(
        documentId=doc_id,
        body={
            "requests": [
                {
                    "insertText": {
                        "location": {"index": end_index},
                        "text": f"\n{text}",
                    }
                }
            ]
        },
    ).execute()

    url = f"https://docs.google.com/document/d/{doc_id}/edit"
    logger.info("Appended to document: %s", doc_id)
    return {
        "document_id": doc_id,
        "message": f"Text appended to document. {url}",
        "url": url,
    }


if __name__ == "__main__":
    mcp.run()
