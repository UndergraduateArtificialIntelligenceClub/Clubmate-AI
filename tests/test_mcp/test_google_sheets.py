"""Tests for mcp_servers.google_sheets — pure helpers and tool functions."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_servers.google_sheets import _extract_sheet_id


class TestExtractSheetId:
    def test_extracts_from_url(self):
        url = "https://docs.google.com/spreadsheets/d/ABC123XYZ/edit"
        assert _extract_sheet_id(url) == "ABC123XYZ"

    def test_extracts_from_url_with_gid(self):
        url = "https://docs.google.com/spreadsheets/d/ABC123XYZ/edit#gid=0"
        assert _extract_sheet_id(url) == "ABC123XYZ"

    def test_returns_bare_id(self):
        assert _extract_sheet_id("ABC123XYZ") == "ABC123XYZ"

    def test_empty_string(self):
        assert _extract_sheet_id("") == ""


class TestReadSheet:
    @patch("mcp_servers.google_sheets.get_service")
    def test_reads_data(self, mock_get_service):
        from mcp_servers.google_sheets import read_sheet
        service = MagicMock()
        service.spreadsheets().values().get().execute.return_value = {
            "values": [["Name", "Age"], ["Alice", "25"], ["Bob", "30"]],
            "range": "Sheet1!A1:B3",
        }
        mock_get_service.return_value = service

        result = read_sheet("ABC123")
        assert result["row_count"] == 3
        assert result["rows"][0] == ["Name", "Age"]

    @patch("mcp_servers.google_sheets.get_service")
    def test_empty_sheet(self, mock_get_service):
        from mcp_servers.google_sheets import read_sheet
        service = MagicMock()
        service.spreadsheets().values().get().execute.return_value = {}
        mock_get_service.return_value = service

        result = read_sheet("ABC123")
        assert result["row_count"] == 0
        assert result["rows"] == []


class TestAppendRows:
    @patch("mcp_servers.google_sheets.get_service")
    def test_appends_rows(self, mock_get_service):
        from mcp_servers.google_sheets import append_rows
        service = MagicMock()
        service.spreadsheets().values().append().execute.return_value = {
            "updates": {"updatedRange": "Sheet1!A4:B5"}
        }
        mock_get_service.return_value = service

        result = append_rows("ABC123", [["Alice", "25"], ["Bob", "30"]])
        assert result["rows_added"] == 2
        assert "ABC123" in result["message"]


class TestWriteRange:
    @patch("mcp_servers.google_sheets.get_service")
    def test_writes_data(self, mock_get_service):
        from mcp_servers.google_sheets import write_range
        service = MagicMock()
        service.spreadsheets().values().update().execute.return_value = {
            "updatedRange": "Sheet1!A1:B2",
            "updatedCells": 4,
        }
        mock_get_service.return_value = service

        result = write_range("ABC123", "Sheet1!A1:B2", [["a", "b"], ["c", "d"]])
        assert result["cells_updated"] == 4


class TestCreateSpreadsheet:
    @patch("mcp_servers.google_sheets.get_service")
    def test_creates_spreadsheet(self, mock_get_service):
        from mcp_servers.google_sheets import create_spreadsheet
        service = MagicMock()
        service.spreadsheets().create().execute.return_value = {"spreadsheetId": "new-sheet-id"}
        mock_get_service.return_value = service

        result = create_spreadsheet("My Sheet")
        assert result["spreadsheet_id"] == "new-sheet-id"
        assert result["title"] == "My Sheet"
