"""Tests for bot/commands/member.py helper functions"""

import sys
from pathlib import Path
from datetime import datetime

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from bot.commands.member import _split, _format_day_events


class TestSplit:
    def test_short_text_single_chunk(self):
        assert _split("hello") == ["hello"]

    def test_empty_string(self):
        assert _split("") == []

    def test_exact_limit(self):
        text = "a" * 1900
        result = _split(text)
        assert len(result) == 1
        assert result[0] == text

    def test_over_limit(self):
        text = "a" * 3000
        result = _split(text)
        assert len(result) == 2
        assert len(result[0]) == 1900
        assert len(result[1]) == 1100

    def test_custom_limit(self):
        text = "abcdefghij"
        result = _split(text, limit=3)
        assert result == ["abc", "def", "ghi", "j"]

    def test_preserves_content(self):
        text = "Hello World"
        assert "".join(_split(text)) == text


class TestFormatDayEvents:
    def test_error_result(self):
        result = {"error": "Calendar unavailable"}
        output = _format_day_events(result)
        assert "Calendar unavailable" in output
        assert "❌" in output

    def test_no_events(self):
        result = {"events": [], "message": "No events."}
        assert _format_day_events(result) == "No events."

    def test_no_events_default_message(self):
        result = {"events": None}
        assert _format_day_events(result) == "No events found for that day."

    def test_single_event_with_attendees(self):
        result = {
            "date": "2025-03-15",
            "timezone": "America/Edmonton",
            "events": [
                {
                    "start": "2025-03-15T14:00:00-06:00",
                    "end": "2025-03-15T15:00:00-06:00",
                    "summary": "Team Standup",
                    "attendees": ["a@test.com"],
                }
            ],
        }
        output = _format_day_events(result)
        assert "Team Standup" in output
        assert "👥 1" in output
        assert "15/03/2025" in output

    def test_event_without_attendees(self):
        result = {
            "date": "2025-03-15",
            "timezone": "America/Edmonton",
            "events": [
                {
                    "start": "2025-03-15T10:00:00-06:00",
                    "end": "2025-03-15T11:00:00-06:00",
                    "summary": "Solo Work",
                }
            ],
        }
        output = _format_day_events(result)
        assert "Solo Work" in output
        assert "👥" not in output

    def test_all_day_event(self):
        result = {
            "date": "2025-12-25",
            "timezone": "America/Edmonton",
            "events": [
                {
                    "start": "2025-12-25",
                    "end": "2025-12-25",
                    "summary": "Christmas",
                }
            ],
        }
        output = _format_day_events(result)
        assert "Christmas" in output

    def test_event_with_missing_times(self):
        result = {
            "date": "2025-03-15",
            "events": [
                {
                    "start": "",
                    "end": "",
                    "summary": "Mystery Event",
                }
            ],
        }
        output = _format_day_events(result)
        assert "Mystery Event" in output

    def test_unparseable_time_falls_back(self):
        result = {
            "date": "2025-03-15",
            "events": [
                {
                    "start": "2025-03-15Tnot-a-time",
                    "end": "2025-03-15Talso-not-a-time",
                    "summary": "Weird Event",
                }
            ],
        }
        output = _format_day_events(result)
        assert "2025-03-15Tnot-a-time" in output
        assert "2025-03-15Talso-not-a-time" in output

    def test_multiple_events(self):
        result = {
            "date": "2025-03-15",
            "timezone": "America/Edmonton",
            "events": [
                {"start": "2025-03-15T09:00:00-06:00", "end": "2025-03-15T10:00:00-06:00", "summary": "First"},
                {"start": "2025-03-15T14:00:00-06:00", "end": "2025-03-15T15:00:00-06:00", "summary": "Second"},
            ],
        }
        output = _format_day_events(result)
        assert "First" in output
        assert "Second" in output
        lines = output.strip().split("\n")
        assert len(lines) == 3  # header + 2 events

    def test_missing_summary_defaults(self):
        result = {
            "date": "2025-03-15",
            "events": [
                {
                    "start": "2025-03-15T10:00:00-06:00",
                    "end": "2025-03-15T11:00:00-06:00",
                }
            ],
        }
        output = _format_day_events(result)
        assert "No Title" in output
