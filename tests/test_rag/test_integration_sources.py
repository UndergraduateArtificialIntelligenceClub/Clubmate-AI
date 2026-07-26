"""Integration tests for file upload and Google Doc ingestion sources.

Tests the full pipeline: raw bytes → temp file → real ChromaDB → retrieve.
Only external APIs (Google) are mocked.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

SAMPLE_CONTENT = (
    "Clubmate AI meeting notes from March 2025. "
    "The team discussed the new RAG integration feature. "
    "Action items: finalize ChromaDB setup, test semantic chunking, "
    "deploy the admin dashboard. Next meeting scheduled for Friday."
)


class TestFileUploadPipeline:
    """Test ingest_uploaded_file with a real ChromaDB backend."""

    def test_txt_upload_ingest_retrieve(self, rag_with_temp_db):
        from ragbot.sources.file_upload import ingest_uploaded_file
        from ragbot.rag import rag_retrieve

        result = ingest_uploaded_file("meeting-notes.txt", SAMPLE_CONTENT.encode())
        assert result is True

        chunks = rag_retrieve("RAG integration")
        assert len(chunks) > 0
        # Source is the temp file name (suffix preserved), not the original filename
        assert chunks[0]["source"].endswith(".txt")

    def test_md_upload_ingest(self, rag_with_temp_db):
        from ragbot.sources.file_upload import ingest_uploaded_file
        from ragbot.rag import rag_has_documents

        md_content = "# Meeting Notes\n\nDiscussed the new RAG pipeline.\n"
        result = ingest_uploaded_file("notes.md", md_content.encode())
        assert result is True
        assert rag_has_documents() is True

    def test_unsupported_extension_raises(self, rag_with_temp_db):
        from ragbot.sources.file_upload import ingest_uploaded_file

        with pytest.raises(ValueError, match="Unsupported file type"):
            ingest_uploaded_file("script.exe", b"binary content")

    def test_temp_file_cleaned_up(self, rag_with_temp_db):
        from ragbot.sources.file_upload import ingest_uploaded_file

        captured = []
        original_ingest = None

        def capture_path(path):
            captured.append(path)
            return True

        with patch("ragbot.rag.rag_ingest", side_effect=capture_path):
            ingest_uploaded_file("temp.txt", b"content")

        assert len(captured) == 1
        assert not Path(captured[0]).exists()


class TestGoogleDocIngestionPipeline:
    """Test ingest_google_doc with a real ChromaDB but mocked Google API."""

    def _mock_docs_service(self, paragraphs=None, headers=None, footers=None, tables=None):
        """Build a mock Google Docs service returning structured content."""
        body_content = []
        for p in (paragraphs or []):
            body_content.append({
                "paragraph": {
                    "elements": [{"textRun": {"content": p}}]
                }
            })
        for t in (tables or []):
            rows = []
            for row_cells in t:
                cells = []
                for cell_text in row_cells:
                    cells.append({
                        "content": [{
                            "paragraph": {
                                "elements": [{"textRun": {"content": cell_text}}]
                            }
                        }]
                    })
                rows.append({"tableCells": cells})
            body_content.append({"table": {"tableRows": rows}})

        doc = {
            "title": "Test Document",
            "body": {"content": body_content},
        }
        if headers:
            doc["headers"] = {
                f"h{i}": {"content": [{"paragraph": {"elements": [{"textRun": {"content": h}}]}}]}
                for i, h in enumerate(headers, 1)
            }
        if footers:
            doc["footers"] = {
                f"f{i}": {"content": [{"paragraph": {"elements": [{"textRun": {"content": f}}]}}]}
                for i, f in enumerate(footers, 1)
            }

        service = MagicMock()
        service.documents().get().execute.return_value = doc
        return service

    def test_ingest_doc_with_paragraphs(self, rag_with_temp_db):
        from ragbot.rag import rag_retrieve

        service = self._mock_docs_service(
            paragraphs=[
                "Clubmate AI is a Discord bot for university clubs.",
                "It provides meeting transcription and RAG knowledge base.",
                "The admin dashboard allows managing settings and documents.",
            ]
        )

        with patch("mcp_servers.google_auth.get_service", return_value=service):
            from ragbot.sources.google_docs import ingest_google_doc
            result = ingest_google_doc("https://docs.google.com/document/d/abc123/edit")

        assert result is True

        chunks = rag_retrieve("meeting transcription")
        assert len(chunks) > 0
        # Content from the mocked doc should be retrievable
        all_text = " ".join(c["content"] for c in chunks)
        assert "Clubmate AI" in all_text

    def test_ingest_doc_with_table(self, rag_with_temp_db):
        from ragbot.rag import rag_retrieve

        service = self._mock_docs_service(
            paragraphs=["Project status:"],
            tables=[["Task", "Status"], ["RAG Setup", "Done"], ["Dashboard", "In Progress"]],
        )

        with patch("mcp_servers.google_auth.get_service", return_value=service):
            from ragbot.sources.google_docs import ingest_google_doc
            result = ingest_google_doc("abc123")

        assert result is True
        chunks = rag_retrieve("RAG Setup status")
        assert len(chunks) > 0
        all_text = " ".join(c["content"] for c in chunks)
        assert "RAG Setup" in all_text

    def test_ingest_doc_with_headers_and_footers(self, rag_with_temp_db):
        from ragbot.rag import rag_retrieve

        service = self._mock_docs_service(
            paragraphs=["Main body content."],
            headers=["Clubmate AI — Meeting Notes"],
            footers=["Confidential — Exec Only"],
        )

        with patch("mcp_servers.google_auth.get_service", return_value=service):
            from ragbot.sources.google_docs import ingest_google_doc
            result = ingest_google_doc("abc123")

        assert result is True
        chunks = rag_retrieve("meeting notes confidential")
        all_text = " ".join(c["content"] for c in chunks)
        assert "Clubmate AI" in all_text
        assert "Confidential" in all_text

    def test_empty_doc_returns_false(self, rag_with_temp_db):
        service = MagicMock()
        service.documents().get().execute.return_value = {
            "title": "Empty",
            "body": {"content": []},
        }

        # Make Drive fallback also fail so the doc truly has no text
        def side_effect(svc_name, version):
            if svc_name == "docs":
                return service
            raise Exception("Drive not configured")

        with patch("mcp_servers.google_auth.get_service", side_effect=side_effect):
            from ragbot.sources.google_docs import ingest_google_doc
            result = ingest_google_doc("abc123")

        assert result is False

    def test_fetch_failure_raises_runtime_error(self, rag_with_temp_db):
        with patch("mcp_servers.google_auth.get_service", side_effect=Exception("Not found")):
            from ragbot.sources.google_docs import ingest_google_doc
            with pytest.raises(RuntimeError, match="Not found"):
                ingest_google_doc("abc123")

    def test_drive_export_fallback(self, rag_with_temp_db):
        """When the structured body is empty, falls back to Drive text export."""
        docs_service = MagicMock()
        docs_service.documents().get().execute.return_value = {
            "title": "Sparse Doc",
            "body": {"content": []},
        }
        drive_service = MagicMock()
        drive_service.files().export().execute.return_value = b"Exported content from Drive"

        def side_effect(service_name, version):
            if service_name == "docs":
                return docs_service
            return drive_service

        with patch("mcp_servers.google_auth.get_service", side_effect=side_effect):
            from ragbot.sources.google_docs import ingest_google_doc
            result = ingest_google_doc("abc123")

        assert result is True
        from ragbot.rag import rag_retrieve
        chunks = rag_retrieve("Exported content")
        assert len(chunks) > 0
