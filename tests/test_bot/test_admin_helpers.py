"""Tests for bot/commands/admin.py helper functions"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from bot.commands.admin import _time_for_date, _format_day_schedule, _format_calendar_result


class TestTimeForDate:
    def test_hhmm_adds_seconds(self):
        assert _time_for_date("2025-03-15", "14:30") == "2025-03-15T14:30:00"

    def test_hhmmss_passthrough(self):
        assert _time_for_date("2025-03-15", "14:30:00") == "2025-03-15T14:30:00"

    def test_full_datetime_passthrough(self):
        assert _time_for_date("2025-03-15", "2025-03-15T14:30:00") == "2025-03-15T14:30:00"

    def test_unknown_format_passthrough(self):
        assert _time_for_date("2025-03-15", "next Tuesday") == "next Tuesday"

    def test_strips_whitespace(self):
        assert _time_for_date("2025-03-15", "  14:30  ") == "2025-03-15T14:30:00"


class TestFormatDaySchedule:
    def test_error_result(self):
        result = {"error": "Calendar not connected"}
        assert "Calendar not connected" in _format_day_schedule(result)
        assert "❌" in _format_day_schedule(result)

    def test_no_events(self):
        result = {"events": [], "message": "No events found."}
        assert _format_day_schedule(result) == "No events found."

    def test_events_with_attendees(self):
        result = {
            "date": "2025-03-15",
            "timezone": "America/Edmonton",
            "events": [
                {
                    "start": "14:00",
                    "end": "15:00",
                    "summary": "Team Meeting",
                    "attendees": ["a@test.com", "b@test.com"],
                }
            ],
        }
        output = _format_day_schedule(result)
        assert "Team Meeting" in output
        assert "👥 2" in output
        assert "2025-03-15" in output

    def test_event_without_attendees(self):
        result = {
            "date": "2025-03-15",
            "timezone": "America/Edmonton",
            "events": [
                {
                    "start": "10:00",
                    "end": "11:00",
                    "summary": "Solo Meeting",
                }
            ],
        }
        output = _format_day_schedule(result)
        assert "Solo Meeting" in output
        assert "👥" not in output

    def test_no_events_with_message(self):
        result = {"events": None, "message": "Nothing on that day."}
        assert _format_day_schedule(result) == "Nothing on that day."


class TestFormatCalendarResult:
    def test_error_with_matches(self):
        result = {
            "error": "Multiple matches found",
            "meetings": [
                {"summary": "Meeting A", "start": "10:00", "end": "11:00"},
                {"summary": "Meeting B", "start": "14:00", "end": "15:00"},
            ],
        }
        output = _format_calendar_result(result)
        assert "Multiple matches found" in output
        assert "Meeting A" in output
        assert "Meeting B" in output

    def test_error_without_matches(self):
        result = {"error": "No matching meeting found"}
        output = _format_calendar_result(result)
        assert "No matching meeting found" in output
        assert "❌" in output

    def test_success_message(self):
        result = {"message": "Meeting cancelled."}
        assert _format_calendar_result(result) == "Meeting cancelled."

    def test_fallback_to_str(self):
        result = {"status": "ok"}
        assert _format_calendar_result(result) == str(result)
