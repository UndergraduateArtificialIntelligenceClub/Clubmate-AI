"""
Google Calendar MCP Server for Clubmate AI.
Provides tools for scheduling, cancelling, rescheduling meetings and managing invites.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

from dateutil import parser, tz
from fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mcp_servers.google_auth import get_service

logger = logging.getLogger(__name__)
mcp = FastMCP("Google Calendar")

DEFAULT_TIMEZONE = "America/Edmonton"


def _normalize_time(t: str, timezone: str) -> str:
    """Convert any timestamp (with or without Z/offset) to a clean ISO local datetime string."""
    dt = parser.isoparse(t)
    target_tz = tz.gettz(timezone)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=target_tz)
    else:
        dt = dt.astimezone(target_tz)
    return dt.replace(microsecond=0).isoformat()


def _find_meeting(
    meeting_name: str,
    date: str,
    calendar_id: str = "primary",
    timezone: str = DEFAULT_TIMEZONE,
) -> dict:
    """
    Internal helper: find a meeting by name + date.
    Returns dict with 'meeting' key on single match, 'multiple_matches' on ambiguity, 'error' on failure.
    """
    try:
        service = get_service("calendar", "v3")
        target_tz = tz.gettz(timezone) or tz.gettz(DEFAULT_TIMEZONE)
        search_date = parser.parse(date).date()

        dt_start = datetime.combine(search_date, datetime.min.time()).replace(tzinfo=target_tz)
        dt_end = datetime.combine(search_date, datetime.max.time()).replace(tzinfo=target_tz)

        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=dt_start.isoformat(),
                timeMax=dt_end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            return {"error": f"No meetings found on {search_date}"}

        matches = [
            {
                "event_id": e["id"],
                "summary": e.get("summary", "No Title"),
                "start": e["start"].get("dateTime", e["start"].get("date")),
                "end": e["end"].get("dateTime", e["end"].get("date")),
            }
            for e in events
            if meeting_name.lower() in e.get("summary", "").lower()
        ]

        if not matches:
            all_names = [e.get("summary", "No Title") for e in events]
            return {
                "error": f"No meeting named '{meeting_name}' on {search_date}. "
                f"Available: {', '.join(all_names)}"
            }

        if len(matches) == 1:
            return {"meeting": matches[0]}

        return {"multiple_matches": True, "meetings": matches}

    except Exception as e:
        return {"error": f"Failed to find meeting: {e}"}


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def schedule_meeting(
    start_time: str,
    end_time: str,
    summary: str,
    attendees: Optional[Union[str, List[str]]] = None,
    calendar_id: str = "primary",
    timezone: str = DEFAULT_TIMEZONE,
) -> dict:
    """
    Schedule a meeting on Google Calendar and send invites to attendees.

    Args:
        start_time: Start time (local ISO format preferred, e.g. '2026-03-15T14:00:00')
        end_time: End time (local ISO format preferred)
        summary: Meeting title/name
        attendees: Email address(es) to invite — string or list of strings
        calendar_id: Calendar ID (default: 'primary')
        timezone: Timezone name (default: 'America/Edmonton')
    """
    if attendees is None:
        attendees_list: List[str] = []
    elif isinstance(attendees, str):
        attendees_list = [a.strip() for a in attendees.split(",")]
    else:
        attendees_list = attendees

    start_local = _normalize_time(start_time, timezone)
    end_local = _normalize_time(end_time, timezone)

    service = get_service("calendar", "v3")
    event = {
        "summary": summary,
        "start": {"dateTime": start_local, "timeZone": timezone},
        "end": {"dateTime": end_local, "timeZone": timezone},
        "attendees": [{"email": e} for e in attendees_list],
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 24 * 60},
                {"method": "popup", "minutes": 10},
            ],
        },
    }

    created = service.events().insert(
        calendarId=calendar_id, body=event, sendUpdates="all"
    ).execute()

    link = created.get("htmlLink", "")
    logger.info("Created event: %s", created.get("id"))
    return {
        "event_id": created.get("id"),
        "link": link,
        "message": f"Meeting '{summary}' scheduled from {start_local} to {end_local}. {link}",
    }


@mcp.tool()
def cancel_meeting(
    event_id: Optional[str] = None,
    meeting_name: Optional[str] = None,
    date: Optional[str] = None,
    calendar_id: str = "primary",
    timezone: str = DEFAULT_TIMEZONE,
) -> dict:
    """
    Cancel a meeting. Provide event_id directly, or meeting_name + date to look it up.

    Args:
        event_id: Google Calendar event ID (optional if meeting_name + date provided)
        meeting_name: Meeting title to search for (partial match, case-insensitive)
        date: Date of the meeting (e.g. '2026-03-15')
        calendar_id: Calendar ID (default: 'primary')
        timezone: Timezone for date lookup
    """
    if not event_id:
        if not meeting_name or not date:
            return {"error": "Provide event_id, or both meeting_name and date"}
        result = _find_meeting(meeting_name, date, calendar_id, timezone)
        if "error" in result:
            return result
        if result.get("multiple_matches"):
            return {"error": "Multiple matches found. Be more specific.", "meetings": result["meetings"]}
        event_id = result["meeting"]["event_id"]

    service = get_service("calendar", "v3")
    event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
    summary = event.get("summary", "Untitled")
    service.events().delete(calendarId=calendar_id, eventId=event_id, sendUpdates="all").execute()

    logger.info("Cancelled event: %s", event_id)
    return {"message": f"Meeting '{summary}' cancelled successfully.", "event_id": event_id}


@mcp.tool()
def reschedule_meeting(
    new_start_time: str,
    new_end_time: str,
    event_id: Optional[str] = None,
    meeting_name: Optional[str] = None,
    original_date: Optional[str] = None,
    calendar_id: str = "primary",
    timezone: str = DEFAULT_TIMEZONE,
) -> dict:
    """
    Reschedule a meeting to a new time. Provide event_id directly, or meeting_name + original_date.

    Args:
        new_start_time: New start time (local ISO format preferred)
        new_end_time: New end time (local ISO format preferred)
        event_id: Google Calendar event ID (optional)
        meeting_name: Meeting title to search for (optional)
        original_date: Date of the meeting to find (optional)
        calendar_id: Calendar ID
        timezone: Timezone name
    """
    if not event_id:
        if not meeting_name or not original_date:
            return {"error": "Provide event_id, or both meeting_name and original_date"}
        result = _find_meeting(meeting_name, original_date, calendar_id, timezone)
        if "error" in result:
            return result
        if result.get("multiple_matches"):
            return {"error": "Multiple matches found. Be more specific.", "meetings": result["meetings"]}
        event_id = result["meeting"]["event_id"]

    start_local = _normalize_time(new_start_time, timezone)
    end_local = _normalize_time(new_end_time, timezone)

    service = get_service("calendar", "v3")
    event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
    old_summary = event.get("summary", "Untitled")

    event["start"] = {"dateTime": start_local, "timeZone": timezone}
    event["end"] = {"dateTime": end_local, "timeZone": timezone}

    updated = service.events().update(
        calendarId=calendar_id, eventId=event_id, body=event, sendUpdates="all"
    ).execute()

    link = updated.get("htmlLink", "")
    logger.info("Rescheduled event: %s", event_id)
    return {
        "link": link,
        "message": f"Meeting '{old_summary}' rescheduled to {start_local} – {end_local}. {link}",
    }


@mcp.tool()
def add_invites(
    new_attendees: List[str],
    event_id: Optional[str] = None,
    meeting_name: Optional[str] = None,
    date: Optional[str] = None,
    calendar_id: str = "primary",
    timezone: str = DEFAULT_TIMEZONE,
) -> dict:
    """
    Add attendees to an existing meeting. Skips anyone already invited.

    Args:
        new_attendees: List of email addresses to add
        event_id: Google Calendar event ID (optional)
        meeting_name: Meeting title to search for (optional)
        date: Date of the meeting (optional)
        calendar_id: Calendar ID
        timezone: Timezone for date lookup
    """
    if not event_id:
        if not meeting_name or not date:
            return {"error": "Provide event_id, or both meeting_name and date"}
        result = _find_meeting(meeting_name, date, calendar_id, timezone)
        if "error" in result:
            return result
        if result.get("multiple_matches"):
            return {"error": "Multiple matches found. Be more specific.", "meetings": result["meetings"]}
        event_id = result["meeting"]["event_id"]

    service = get_service("calendar", "v3")
    event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
    summary = event.get("summary", "Untitled")

    current_attendees = event.get("attendees", [])
    current_emails = {a.get("email") for a in current_attendees}

    added, duplicates = [], []
    for email in new_attendees:
        email = email.strip()
        if email in current_emails:
            duplicates.append(email)
        else:
            current_attendees.append({"email": email})
            added.append(email)

    if not added:
        msg = "No new attendees added."
        if duplicates:
            msg += f" Already invited: {', '.join(duplicates)}."
        return {"message": msg}

    event["attendees"] = current_attendees
    updated = service.events().update(
        calendarId=calendar_id, eventId=event_id, body=event, sendUpdates="all"
    ).execute()

    link = updated.get("htmlLink", "")
    msg = f"Added {', '.join(added)} to '{summary}'."
    if duplicates:
        msg += f" Already invited: {', '.join(duplicates)}."
    return {"link": link, "message": f"{msg} {link}"}


@mcp.tool()
def list_upcoming_events(max_results: int = 10, calendar_id: str = "primary") -> str:
    """
    List the next N upcoming events on the calendar.

    Args:
        max_results: Number of events to return (default: 10)
        calendar_id: Calendar ID (default: 'primary')
    """
    service = get_service("calendar", "v3")
    now = datetime.utcnow().isoformat() + "Z"
    result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = result.get("items", [])
    if not events:
        return "No upcoming events."
    lines = []
    for e in events:
        start = e["start"].get("dateTime", e["start"].get("date"))
        lines.append(f"{start} — {e.get('summary', '(No title)')}")
    return "\n".join(lines)


@mcp.tool()
def check_availability(
    start_time: str, end_time: str, calendar_id: str = "primary"
) -> str:
    """
    Check if a time slot is free on the calendar.

    Args:
        start_time: ISO format start (e.g. '2026-03-15T09:00:00Z')
        end_time: ISO format end
        calendar_id: Calendar ID (default: 'primary')
    """
    service = get_service("calendar", "v3")
    result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = result.get("items", [])
    if not events:
        return "Time slot is free — no conflicting events."
    lines = ["Busy — conflicting events:"]
    for e in events:
        start = e["start"].get("dateTime", e["start"].get("date"))
        lines.append(f"  - {start}: {e.get('summary', 'No Title')}")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
