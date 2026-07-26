"""Tests for mcp_servers.google_calendar — pure helpers and tool functions."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


class TestNormalizeTime:
    def _import_fn(self):
        from mcp_servers.google_calendar import _normalize_time
        return _normalize_time

    def test_utc_to_local(self):
        fn = self._import_fn()
        result = fn("2026-03-15T18:00:00Z", "America/Edmonton")
        # UTC 18:00 in March (MDT = UTC-6) = 12:00 local
        assert "12:00" in result

    def test_naive_datetime_gets_timezone(self):
        fn = self._import_fn()
        result = fn("2026-03-15T14:00:00", "America/Edmonton")
        assert "14:00" in result

    def test_strips_microseconds(self):
        fn = self._import_fn()
        result = fn("2026-03-15T14:00:00.123456", "America/Edmonton")
        assert "." not in result


class TestDayBounds:
    def _import_fn(self):
        from mcp_servers.google_calendar import _day_bounds
        return _day_bounds

    def test_returns_correct_structure(self):
        fn = self._import_fn()
        date_obj, start, end = fn("2026-03-15", "America/Edmonton")
        assert str(date_obj) == "2026-03-15"
        assert "2026-03-15" in start
        assert "2026-03-15" in end

    def test_start_before_end(self):
        fn = self._import_fn()
        _, start, end = fn("2026-06-21", "America/Edmonton")
        assert start < end


class TestFindMeeting:
    @patch("mcp_servers.google_calendar.get_service")
    def test_no_events_found(self, mock_get_service):
        from mcp_servers.google_calendar import _find_meeting
        service = MagicMock()
        service.events().list().execute.return_value = {"items": []}
        mock_get_service.return_value = service

        result = _find_meeting("Standup", "2026-03-15")
        assert "error" in result
        assert "No meetings found" in result["error"]

    @patch("mcp_servers.google_calendar.get_service")
    def test_single_match(self, mock_get_service):
        from mcp_servers.google_calendar import _find_meeting
        service = MagicMock()
        service.events().list().execute.return_value = {
            "items": [{"id": "evt1", "summary": "Standup", "start": {"dateTime": "2026-03-15T10:00"}, "end": {"dateTime": "2026-03-15T10:30"}}]
        }
        mock_get_service.return_value = service

        result = _find_meeting("Standup", "2026-03-15")
        assert "meeting" in result
        assert result["meeting"]["event_id"] == "evt1"

    @patch("mcp_servers.google_calendar.get_service")
    def test_multiple_matches(self, mock_get_service):
        from mcp_servers.google_calendar import _find_meeting
        service = MagicMock()
        service.events().list().execute.return_value = {
            "items": [
                {"id": "evt1", "summary": "Team Standup", "start": {"dateTime": "2026-03-15T10:00"}, "end": {"dateTime": "2026-03-15T10:30"}},
                {"id": "evt2", "summary": "Project Standup", "start": {"dateTime": "2026-03-15T14:00"}, "end": {"dateTime": "2026-03-15T14:30"}},
            ]
        }
        mock_get_service.return_value = service

        result = _find_meeting("Standup", "2026-03-15")
        assert result.get("multiple_matches") is True
        assert len(result["meetings"]) == 2

    @patch("mcp_servers.google_calendar.get_service")
    def test_no_name_match(self, mock_get_service):
        from mcp_servers.google_calendar import _find_meeting
        service = MagicMock()
        service.events().list().execute.return_value = {
            "items": [{"id": "evt1", "summary": "Lunch", "start": {"dateTime": "2026-03-15T12:00"}, "end": {"dateTime": "2026-03-15T13:00"}}]
        }
        mock_get_service.return_value = service

        result = _find_meeting("Standup", "2026-03-15")
        assert "error" in result
        assert "No meeting named" in result["error"]


class TestListEventsOnDate:
    @patch("mcp_servers.google_calendar.get_service")
    def test_returns_formatted_events(self, mock_get_service):
        from mcp_servers.google_calendar import list_events_on_date
        service = MagicMock()
        service.events().list().execute.return_value = {
            "items": [
                {
                    "id": "evt1",
                    "summary": "Standup",
                    "start": {"dateTime": "2026-03-15T10:00:00"},
                    "end": {"dateTime": "2026-03-15T10:30:00"},
                    "attendees": [{"email": "a@test.com"}],
                    "location": "Room 101",
                    "htmlLink": "https://calendar.google.com/evt1",
                }
            ]
        }
        mock_get_service.return_value = service

        result = list_events_on_date("2026-03-15")
        assert result["total_events"] == 1
        assert result["events"][0]["summary"] == "Standup"
        assert "a@test.com" in result["events"][0]["attendees"]

    @patch("mcp_servers.google_calendar.get_service")
    def test_empty_day(self, mock_get_service):
        from mcp_servers.google_calendar import list_events_on_date
        service = MagicMock()
        service.events().list().execute.return_value = {"items": []}
        mock_get_service.return_value = service

        result = list_events_on_date("2026-12-25")
        assert result["total_events"] == 0
        assert "No events" in result["message"]


class TestScheduleMeeting:
    @patch("mcp_servers.google_calendar.get_service")
    def test_creates_event(self, mock_get_service):
        from mcp_servers.google_calendar import schedule_meeting
        service = MagicMock()
        service.events().insert().execute.return_value = {
            "id": "new-event",
            "htmlLink": "https://calendar.google.com/new",
        }
        mock_get_service.return_value = service

        result = schedule_meeting("2026-03-15T14:00:00", "2026-03-15T15:00:00", "Team Meeting")
        assert result["event_id"] == "new-event"
        assert "Team Meeting" in result["message"]

    @patch("mcp_servers.google_calendar.get_service")
    def test_with_string_attendees(self, mock_get_service):
        from mcp_servers.google_calendar import schedule_meeting
        service = MagicMock()
        service.events().insert().execute.return_value = {"id": "evt", "htmlLink": "link"}
        mock_get_service.return_value = service

        result = schedule_meeting(
            "2026-03-15T14:00:00", "2026-03-15T15:00:00", "Meeting",
            attendees="a@test.com, b@test.com"
        )
        assert "event_id" in result


class TestCancelMeeting:
    @patch("mcp_servers.google_calendar.get_service")
    def test_cancel_by_event_id(self, mock_get_service):
        from mcp_servers.google_calendar import cancel_meeting
        service = MagicMock()
        service.events().get().execute.return_value = {"summary": "Old Meeting"}
        mock_get_service.return_value = service

        result = cancel_meeting(event_id="evt123")
        assert "cancelled" in result["message"]
        assert result["event_id"] == "evt123"

    def test_cancel_without_params(self):
        from mcp_servers.google_calendar import cancel_meeting
        result = cancel_meeting()
        assert "error" in result


class TestCheckAvailability:
    @patch("mcp_servers.google_calendar.get_service")
    def test_slot_free(self, mock_get_service):
        from mcp_servers.google_calendar import check_availability
        service = MagicMock()
        service.events().list().execute.return_value = {"items": []}
        mock_get_service.return_value = service

        result = check_availability("2026-03-15T09:00:00Z", "2026-03-15T10:00:00Z")
        assert "free" in result.lower()

    @patch("mcp_servers.google_calendar.get_service")
    def test_slot_busy(self, mock_get_service):
        from mcp_servers.google_calendar import check_availability
        service = MagicMock()
        service.events().list().execute.return_value = {
            "items": [{"summary": "Conflict", "start": {"dateTime": "2026-03-15T09:00:00"}}]
        }
        mock_get_service.return_value = service

        result = check_availability("2026-03-15T09:00:00Z", "2026-03-15T10:00:00Z")
        assert "Busy" in result
