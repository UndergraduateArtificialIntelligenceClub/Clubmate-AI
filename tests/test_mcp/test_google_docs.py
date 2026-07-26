"""Tests for mcp_servers.google_docs — pure helpers and tool functions."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_servers.google_docs import (
    _extract_doc_id,
    _read_structural_elements,
)


class TestExtractDocId:
    def test_extracts_from_url(self):
        url = "https://docs.google.com/document/d/ABC123XYZ/edit"
        assert _extract_doc_id(url) == "ABC123XYZ"

    def test_extracts_from_url_with_trailing_slash(self):
        url = "https://docs.google.com/document/d/ABC123/"
        assert _extract_doc_id(url) == "ABC123"

    def test_returns_bare_id(self):
        assert _extract_doc_id("ABC123XYZ") == "ABC123XYZ"

    def test_empty_string(self):
        assert _extract_doc_id("") == ""


class TestReadStructuralElements:
    def test_paragraphs(self):
        elements = [
            {"paragraph": {"elements": [{"textRun": {"content": "Hello "}}, {"textRun": {"content": "World"}}]}}
        ]
        assert _read_structural_elements(elements) == "Hello World"

    def test_tables(self):
        elements = [
            {
                "table": {
                    "tableRows": [
                        {"tableCells": [{"content": [{"paragraph": {"elements": [{"textRun": {"content": "Cell1"}}]}}]}]}
                    ]
                }
            }
        ]
        assert _read_structural_elements(elements) == "Cell1"

    def test_table_of_contents(self):
        elements = [
            {"tableOfContents": {"content": [{"paragraph": {"elements": [{"textRun": {"content": "TOC item"}}]}}]}}
        ]
        assert _read_structural_elements(elements) == "TOC item"

    def test_empty_elements(self):
        assert _read_structural_elements([]) == ""

    def test_mixed_elements(self):
        elements = [
            {"paragraph": {"elements": [{"textRun": {"content": "Text "}}]}},
            {"table": {"tableRows": []}},
            {"paragraph": {"elements": [{"textRun": {"content": "End"}}]}},
        ]
        assert _read_structural_elements(elements) == "Text End"


class TestReadDocument:
    @patch("mcp_servers.google_docs.get_service")
    def test_reads_document(self, mock_get_service):
        from mcp_servers.google_docs import read_document
        service = MagicMock()
        service.documents().get().execute.return_value = {
            "title": "Test Doc",
            "body": {"content": [{"paragraph": {"elements": [{"textRun": {"content": "Hello"}}]}}]},
        }
        mock_get_service.return_value = service

        result = read_document("ABC123")
        assert result["title"] == "Test Doc"
        assert result["document_id"] == "ABC123"
        assert "Hello" in result["content"]


class TestCreateDocument:
    @patch("mcp_servers.google_docs.get_service")
    def test_creates_document(self, mock_get_service):
        from mcp_servers.google_docs import create_document
        service = MagicMock()
        service.documents().create().execute.return_value = {"documentId": "new-doc-id"}
        mock_get_service.return_value = service

        result = create_document("My Doc", "Initial content")
        assert result["document_id"] == "new-doc-id"
        assert result["title"] == "My Doc"
        service.documents().batchUpdate.assert_called_once()

    @patch("mcp_servers.google_docs.get_service")
    def test_creates_empty_document(self, mock_get_service):
        from mcp_servers.google_docs import create_document
        service = MagicMock()
        service.documents().create().execute.return_value = {"documentId": "new-doc-id"}
        mock_get_service.return_value = service

        result = create_document("Empty Doc")
        assert result["document_id"] == "new-doc-id"
        service.documents().batchUpdate.assert_not_called()


class TestAppendToDocument:
    @patch("mcp_servers.google_docs.get_service")
    def test_appends_text(self, mock_get_service):
        from mcp_servers.google_docs import append_to_document
        service = MagicMock()
        service.documents().get().execute.return_value = {
            "body": {"content": [{"endIndex": 10}]}
        }
        mock_get_service.return_value = service

        result = append_to_document("ABC123", "New content")
        assert result["document_id"] == "ABC123"
        service.documents().batchUpdate.assert_called_once()
