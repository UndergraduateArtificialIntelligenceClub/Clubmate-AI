"""Tests for ragbot/sources/google_docs.py"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ragbot.sources.google_docs import _extract_doc_id, _read_elements


class TestExtractDocId:
    def test_extracts_from_full_url(self):
        url = "https://docs.google.com/document/d/abc123def/edit"
        assert _extract_doc_id(url) == "abc123def"

    def test_extracts_from_url_with_trailing_slash(self):
        url = "https://docs.google.com/document/d/xyz789/"
        assert _extract_doc_id(url) == "xyz789"

    def test_returns_bare_id(self):
        assert _extract_doc_id("abc123def") == "abc123def"

    def test_empty_string(self):
        assert _extract_doc_id("") == ""

    def test_non_google_url_returns_as_is(self):
        url = "https://example.com/doc"
        assert _extract_doc_id(url) == url


class TestReadElements:
    def test_paragraphs(self):
        elements = [
            {"paragraph": {"elements": [{"textRun": {"content": "Hello "}}]}},
            {"paragraph": {"elements": [{"textRun": {"content": "world"}}]}},
        ]
        assert _read_elements(elements) == "Hello world"

    def test_table_cells(self):
        elements = [
            {
                "table": {
                    "tableRows": [
                        {
                            "tableCells": [
                                {"content": [{"paragraph": {"elements": [{"textRun": {"content": "A"}}]}}]},
                                {"content": [{"paragraph": {"elements": [{"textRun": {"content": "B"}}]}}]},
                            ]
                        }
                    ]
                }
            }
        ]
        assert _read_elements(elements) == "AB"

    def test_table_of_contents(self):
        elements = [
            {
                "tableOfContents": {
                    "content": [
                        {"paragraph": {"elements": [{"textRun": {"content": "TOC item"}}]}}
                    ]
                }
            }
        ]
        assert _read_elements(elements) == "TOC item"

    def test_empty_elements(self):
        assert _read_elements([]) == ""

    def test_mixed_elements(self):
        elements = [
            {"paragraph": {"elements": [{"textRun": {"content": "Title"}}]}},
            {
                "table": {
                    "tableRows": [
                        {
                            "tableCells": [
                                {"content": [{"paragraph": {"elements": [{"textRun": {"content": "Cell"}}]}}]}
                            ]
                        }
                    ]
                }
            },
        ]
        assert _read_elements(elements) == "TitleCell"

    def test_paragraph_without_text_run(self):
        elements = [{"paragraph": {"elements": [{"image": {"content": ""}}]}}]
        assert _read_elements(elements) == ""

    def test_paragraph_without_elements(self):
        elements = [{"paragraph": {}}]
        assert _read_elements(elements) == ""

    def test_text_run_without_content(self):
        elements = [{"paragraph": {"elements": [{"textRun": {}}]}}]
        assert _read_elements(elements) == ""


class TestFetchGoogleDocText:
    def test_fetches_document(self):
        mock_service = MagicMock()
        mock_service.documents().get().execute.return_value = {
            "title": "My Doc",
            "body": {
                "content": [
                    {"paragraph": {"elements": [{"textRun": {"content": "Document body"}}]}}
                ]
            },
        }
        with patch("mcp_servers.google_auth.get_service", return_value=mock_service):
            from ragbot.sources.google_docs import fetch_google_doc_text
            title, text = fetch_google_doc_text("abc123")
        assert title == "My Doc"
        assert "Document body" in text

    def test_includes_headers_and_footers(self):
        mock_service = MagicMock()
        mock_service.documents().get().execute.return_value = {
            "title": "Doc with Header",
            "body": {"content": []},
            "headers": {
                "h1": {"content": [{"paragraph": {"elements": [{"textRun": {"content": "Header text"}}]}}]}
            },
            "footers": {
                "f1": {"content": [{"paragraph": {"elements": [{"textRun": {"content": "Footer text"}}]}}]}
            },
        }
        with patch("mcp_servers.google_auth.get_service", return_value=mock_service):
            from ragbot.sources.google_docs import fetch_google_doc_text
            title, text = fetch_google_doc_text("abc123")
        assert "Header text" in text
        assert "Footer text" in text

    def test_empty_doc_falls_back_to_drive_export(self):
        mock_docs_service = MagicMock()
        mock_docs_service.documents().get().execute.return_value = {
            "title": "Empty Doc",
            "body": {"content": []},
        }
        mock_drive_service = MagicMock()
        mock_drive_service.files().export().execute.return_value = b"Exported text content"

        def side_effect(service_name, version):
            if service_name == "docs":
                return mock_docs_service
            return mock_drive_service

        with patch("mcp_servers.google_auth.get_service", side_effect=side_effect):
            from ragbot.sources.google_docs import fetch_google_doc_text
            title, text = fetch_google_doc_text("abc123")
        assert text == "Exported text content"

    def test_empty_doc_drive_export_fails(self):
        mock_docs_service = MagicMock()
        mock_docs_service.documents().get().execute.return_value = {
            "title": "Empty Doc",
            "body": {"content": []},
        }
        mock_drive_service = MagicMock()
        mock_drive_service.files().export().execute.side_effect = Exception("Permission denied")

        def side_effect(service_name, version):
            if service_name == "docs":
                return mock_docs_service
            return mock_drive_service

        with patch("mcp_servers.google_auth.get_service", side_effect=side_effect):
            from ragbot.sources.google_docs import fetch_google_doc_text
            title, text = fetch_google_doc_text("abc123")
        assert title == "Empty Doc"
        assert text == ""


class TestIngestGoogleDoc:
    def test_ingest_success(self):
        with patch("ragbot.sources.google_docs.fetch_google_doc_text", return_value=("Title", "Some content")), \
             patch("ragbot.rag.rag_ingest", return_value=True) as mock_ingest:
            from ragbot.sources.google_docs import ingest_google_doc
            result = ingest_google_doc("abc123")
        assert result is True
        mock_ingest.assert_called_once()

    def test_empty_content_returns_false(self):
        with patch("ragbot.sources.google_docs.fetch_google_doc_text", return_value=("Empty", "")):
            from ragbot.sources.google_docs import ingest_google_doc
            result = ingest_google_doc("abc123")
        assert result is False

    def test_fetch_failure_raises(self):
        with patch("ragbot.sources.google_docs.fetch_google_doc_text", side_effect=Exception("Not found")):
            from ragbot.sources.google_docs import ingest_google_doc
            with pytest.raises(RuntimeError, match="Not found"):
                ingest_google_doc("abc123")

    def test_ingest_failure_returns_false(self):
        with patch("ragbot.sources.google_docs.fetch_google_doc_text", return_value=("Title", "Content")), \
             patch("ragbot.rag.rag_ingest", return_value=False):
            from ragbot.sources.google_docs import ingest_google_doc
            result = ingest_google_doc("abc123")
        assert result is False
