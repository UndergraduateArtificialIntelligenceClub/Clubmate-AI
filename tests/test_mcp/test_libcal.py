"""Tests for mcp_servers.libcal — pure helpers and tool functions."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_servers.libcal import (
    parse_slots,
    format_results,
    list_libraries,
    LIBRARIES,
    ROOM_MAPPINGS,
)


class TestParseSlots:
    def test_empty_data(self):
        assert parse_slots({}, "cameron") == {}

    def test_no_slots_key(self):
        assert parse_slots({"other": []}, "cameron") == {}

    def test_parses_available_slots(self):
        data = {
            "slots": [
                {
                    "itemId": 5574,
                    "className": "",
                    "start": "2026-03-15 09:00",
                    "end": "2026-03-15 09:30",
                }
            ]
        }
        result = parse_slots(data, "cameron")
        assert "Available" in result
        assert result["Available"][0]["room"] == "ROOM 1-21"
        assert result["Available"][0]["start"] == "09:00"

    def test_parses_checked_out_slots(self):
        data = {
            "slots": [
                {
                    "itemId": 5574,
                    "className": "s-lc-eq-checkout",
                    "start": "2026-03-15T10:00:00",
                    "end": "2026-03-15T10:30:00",
                }
            ]
        }
        result = parse_slots(data, "cameron")
        assert "Checked Out" in result

    def test_unknown_class_name_defaults_to_available(self):
        data = {
            "slots": [
                {
                    "itemId": 5574,
                    "className": "unknown-class",
                    "start": "2026-03-15 09:00",
                    "end": "2026-03-15 09:30",
                }
            ]
        }
        result = parse_slots(data, "cameron")
        assert "Available" in result

    def test_unknown_room_id(self):
        data = {
            "slots": [
                {
                    "itemId": 9999,
                    "className": "",
                    "start": "2026-03-15 09:00",
                    "end": "2026-03-15 09:30",
                }
            ]
        }
        result = parse_slots(data, "cameron")
        assert "Unknown (9999)" in result["Available"][0]["room"]


class TestFormatResults:
    def test_error_result(self):
        result = format_results({"error": "Something went wrong"})
        assert "Error" in result
        assert "Something went wrong" in result

    def test_no_rooms_available(self):
        results = {
            "library": "Cameron Library",
            "date": "2026-03-15",
            "available_by_room": {},
            "total_available_slots": 0,
        }
        result = format_results(results)
        assert "No rooms available" in result

    def test_formats_with_rooms(self):
        results = {
            "library": "Cameron Library",
            "date": "2026-03-15",
            "available_by_room": {
                "ROOM 1-21": ["09:00-09:30", "09:30-10:00"],
            },
            "total_available_slots": 2,
        }
        result = format_results(results)
        assert "Cameron Library" in result
        assert "ROOM 1-21" in result
        assert "March 15, 2026" in result

    def test_includes_booking_url(self):
        results = {
            "library": "Cameron Library",
            "location": "cameron",
            "date": "2026-03-15",
            "available_by_room": {"ROOM 1-21": ["09:00-09:30"]},
            "total_available_slots": 1,
        }
        result = format_results(results)
        assert "ROOM 1-21" in result

    def test_time_filter_display(self):
        results = {
            "library": "Cameron Library",
            "date": "2026-03-15",
            "time_filter": {"start": "17:00", "end": "19:00"},
            "available_by_room": {},
            "total_available_slots": 0,
        }
        result = format_results(results)
        assert "5:00 PM" in result
        assert "7:00 PM" in result


class TestListLibraries:
    def test_returns_all_libraries(self):
        result = list_libraries()
        assert "libraries" in result
        assert len(result["libraries"]) == len(LIBRARIES)
        ids = [lib["id"] for lib in result["libraries"]]
        assert "cameron" in ids
        assert "sperber" in ids


class TestGetAvailableSlots:
    @patch("mcp_servers.libcal.fetch_availability")
    def test_unknown_library(self, mock_fetch):
        from mcp_servers.libcal import get_available_slots
        result = get_available_slots("unknown")
        assert "Error" in result

    @patch("mcp_servers.libcal.fetch_availability")
    def test_fetch_failure(self, mock_fetch):
        from mcp_servers.libcal import get_available_slots
        mock_fetch.return_value = None
        result = get_available_slots("cameron", formatted=False)
        assert "error" in result

    @patch("mcp_servers.libcal.fetch_availability")
    def test_valid_data(self, mock_fetch):
        from mcp_servers.libcal import get_available_slots
        mock_fetch.return_value = {
            "slots": [
                {"itemId": 5574, "className": "", "start": "2026-03-15 09:00", "end": "2026-03-15 09:30"},
                {"itemId": 5574, "className": "", "start": "2026-03-15 09:30", "end": "2026-03-15 10:00"},
            ]
        }
        result = get_available_slots("cameron", date="2026-03-15", formatted=False)
        assert result["total_available_slots"] == 2
        assert "ROOM 1-21" in result["available_by_room"]

    @patch("mcp_servers.libcal.fetch_availability")
    def test_room_filter(self, mock_fetch):
        from mcp_servers.libcal import get_available_slots
        mock_fetch.return_value = {
            "slots": [
                {"itemId": 5574, "className": "", "start": "2026-03-15 09:00", "end": "2026-03-15 09:30"},
                {"itemId": 3782, "className": "", "start": "2026-03-15 09:00", "end": "2026-03-15 09:30"},
            ]
        }
        result = get_available_slots("cameron", date="2026-03-15", room_filter="B-05", formatted=False)
        assert "ROOM 1-21" not in result["available_by_room"]
        assert "ROOM B-05A" in result["available_by_room"]

    @patch("mcp_servers.libcal.fetch_availability")
    def test_time_filter(self, mock_fetch):
        from mcp_servers.libcal import get_available_slots
        mock_fetch.return_value = {
            "slots": [
                {"itemId": 5574, "className": "", "start": "2026-03-15 09:00", "end": "2026-03-15 09:30"},
                {"itemId": 5574, "className": "", "start": "2026-03-15 17:00", "end": "2026-03-15 17:30"},
            ]
        }
        result = get_available_slots("cameron", date="2026-03-15", start_time="16:00", formatted=False)
        # Only the 17:00 slot should remain
        assert result["total_available_slots"] == 1
