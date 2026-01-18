from fastmcp import FastMCP
from datetime import datetime
import os
from typing import List  

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from typing import Optional, List,Union

from pathlib import Path

# Get the directory where credentials are stored (in project root)
SCRIPT_DIR = Path(__file__).parent.parent.parent  # Points to project root
CREDENTIALS_PATH = SCRIPT_DIR / "credentials.json"
TOKEN_PATH = SCRIPT_DIR / "token.json"

mcp = FastMCP("Google Calendar MCP")

SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
]




from dateutil import parser, tz
import json
import logging

logger = logging.getLogger(__name__)

def normalize_time(t: str, timezone: str) -> str:
    """
    Convert ANY incoming timestamp (with or without Z/offset)
    into a clean ISO local datetime string.
    """
    dt = parser.isoparse(t)  # parses timestamps with or without timezone info
    target_tz = tz.gettz(timezone)

    if dt.tzinfo is None:
        # No tz provided -> treat it as local to the chosen timezone
        dt = dt.replace(tzinfo=target_tz)
    else:
        # Has a timezone/Z -> convert to local timezone
        dt = dt.astimezone(target_tz)

    # Standardize format
    return dt.replace(microsecond=0).isoformat()

@mcp.tool()
def schedule_meeting(
        start_time: str,
        end_time: str,
        summary: str,
        id: Optional[str] = 'primary',
        attendees: Optional[Union[str, List[str]]] = None,
        timezone: Optional[str] = "America/Edmonton",
        ):
    """
    Schedule a meeting on Google Calendar.

    NOTE TO MODEL:
    - Provide start_time and end_time in local time whenever possible.
    - If you provide Z/UTC timestamps, they will be auto-converted.
    """

    # ---- Normalize attendees ----
    if attendees is None:
        attendees_list: List[str] = []
    elif isinstance(attendees, str):
        attendees_list = [attendees.strip()]
    else:
        attendees_list = attendees

    logger.info("schedule_meeting CALLED with raw inputs: %s",
                json.dumps({
                    "start_time": start_time,
                    "end_time": end_time,
                    "summary": summary,
                    "calendar_id": id,
                    "attendees": attendees_list,
                    "timezone": timezone,
                }, indent=2))

    start_local = normalize_time(start_time, timezone)
    end_local   = normalize_time(end_time, timezone)

    logger.info("Normalized times -> start: %s | end: %s",
                start_local, end_local)

    service = get_service()

    event = {
        'summary': summary,
        'start': {
            'dateTime': start_local,
            'timeZone': timezone,
        },
        'end': {
            'dateTime': end_local,
            'timeZone': timezone,
        },
        'attendees': [{'email': email} for email in attendees_list],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ]
        }
    }

    created = service.events().insert(
        calendarId=id,
        body=event,
        sendUpdates='all'
    ).execute()

    logger.info("Created event: %s", json.dumps(created, indent=2))

    link = created.get('htmlLink', 'No link available')

    return {
        "link": link,
        "message": (
            f"Meeting '{summary}' scheduled from {start_local} to {end_local} "
            f"with attendees {attendees_list}, {link}"
        ),
    }

@mcp.tool()
def cancel_meeting(
        event_id: Optional[str] = None,
        meeting_name: Optional[str] = None,
        date: Optional[str] = None,
        calendar_id: Optional[str] = 'primary',
        send_updates: Optional[str] = 'all'
        ):
    """
    Cancel a meeting on Google Calendar.

    NOTE TO MODEL:
    - You can either provide event_id directly, OR provide meeting_name + date to find the meeting.
    - If meeting_name and date are provided, the function will automatically find the meeting.

    Args:
        event_id (str): Optional - The ID of the event to cancel
        meeting_name (str): Optional - Name of the meeting to find and cancel
        date (str): Optional - Date of the meeting
        calendar_id (str): Calendar ID
        send_updates (str): Whether to send cancellation notifications: 'all', 'externalOnly', or 'none'

    Returns:
        dict: A message confirming the cancellation
    """
    try:
        # If event_id not provided, try to find it using meeting_name and date
        if not event_id:
            if not meeting_name or not date:
                return {
                    "error": "Either provide event_id, or both meeting_name and date"
                }

            # Find the meeting
            find_result = find_meeting_by_name_and_date(meeting_name, date, calendar_id)

            if "error" in find_result:
                return find_result

            if find_result.get("multiple_matches"):
                # Multiple meetings found - return them for user to choose
                return {
                    "error": "Multiple meetings found. Please be more specific.",
                    "meetings": find_result["meetings"]
                }

            # Single match found
            event_id = find_result["meeting"]["event_id"]
            logger.info(f"Found meeting '{meeting_name}' with event_id: {event_id}")

        service = get_service()

        # Get the event details before deleting
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        summary = event.get('summary', 'Untitled Event')

        # Delete the event
        service.events().delete(
            calendarId=calendar_id,
            eventId=event_id,
            sendUpdates=send_updates
        ).execute()

        logger.info("Cancelled event: %s (ID: %s)", summary, event_id)

        return {
            "message": f"Meeting '{summary}' has been cancelled successfully.",
            "event_id": event_id
        }
    except Exception as e:
        logger.error("Error cancelling meeting: %s", str(e))
        return {
            "error": f"Failed to cancel meeting: {str(e)}"
        }

@mcp.tool()
def reschedule_meeting(
        new_start_time: str,
        new_end_time: str,
        event_id: Optional[str] = None,
        meeting_name: Optional[str] = None,
        original_date: Optional[str] = None,
        calendar_id: Optional[str] = 'primary',
        timezone: Optional[str] = "America/Edmonton",
        send_updates: Optional[str] = 'all'
        ):
    """
    Reschedule a meeting to a new time.

    NOTE TO MODEL:
    - You can either provide event_id directly, OR provide meeting_name + original_date to find the meeting.
    - If meeting_name and original_date are provided, the function will automatically find the meeting.
    - Provide new_start_time and new_end_time in local time whenever possible.
    - If you provide Z/UTC timestamps, they will be auto-converted.

    Args:
        new_start_time (str): New start time
        new_end_time (str): New end time
        event_id (str): Optional - Event ID of the meeting to be rescheduled
        meeting_name (str): Optional - Name of the meeting to find
        original_date (str): Optional - Date of the meeting to find
        calendar_id (str): Calendar ID
        timezone (str): Timezone name (e.g., 'America/Edmonton', 'America/Vancouver'). Defaults to Mountain Time.
        send_updates (str): Whether to send update notifications: 'all', 'externalOnly', or 'none' (defaults to 'all')

    Returns:
        dict: Link and message about the rescheduled meeting
    """
    try:
        # If event_id not provided, try to find it using meeting_name and original_date
        if not event_id:
            if not meeting_name or not original_date:
                return {
                    "error": "Either provide event_id, or both meeting_name and original_date"
                }

            # Find the meeting
            find_result = find_meeting_by_name_and_date(meeting_name, original_date, calendar_id)

            if "error" in find_result:
                return find_result

            if find_result.get("multiple_matches"):
                # Multiple meetings found - return them for user to choose
                return {
                    "error": "Multiple meetings found. Please be more specific.",
                    "meetings": find_result["meetings"]
                }

            # Single match found
            event_id = find_result["meeting"]["event_id"]
            logger.info(f"Found meeting '{meeting_name}' with event_id: {event_id}")

        logger.info("reschedule_meeting CALLED with raw inputs: %s",
                    json.dumps({
                        "event_id": event_id,
                        "new_start_time": new_start_time,
                        "new_end_time": new_end_time,
                        "calendar_id": calendar_id,
                        "timezone": timezone,
                    }, indent=2))

        # Normalize times to handle timezone conversions
        start_local = normalize_time(new_start_time, timezone)
        end_local = normalize_time(new_end_time, timezone)

        logger.info("Normalized times -> start: %s | end: %s",
                    start_local, end_local)

        service = get_service()

        # Get the existing event
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        old_summary = event.get('summary', 'Untitled Event')

        # Update the event times
        event['start'] = {
            'dateTime': start_local,
            'timeZone': timezone,
        }
        event['end'] = {
            'dateTime': end_local,
            'timeZone': timezone,
        }

        # Update the event on the calendar
        updated_event = service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event,
            sendUpdates=send_updates
        ).execute()

        link = updated_event.get('htmlLink', 'No link available')

        logger.info("Rescheduled event: %s", json.dumps(updated_event, indent=2))

        return {
            "link": link,
            "message": (
                f"Meeting '{old_summary}' rescheduled from {start_local} to {end_local}. "
                f"{link}"
            )
        }
    except Exception as e:
        logger.error("Error rescheduling meeting: %s", str(e))
        return {
            "error": f"Failed to reschedule meeting: {str(e)}"
        }

def add_invites():
    pass

def find_meeting_by_name_and_date(
        meeting_name: str,
        date: str,
        calendar_id: Optional[str] = 'primary'
        ):
    """
    Internal helper function to find a meeting by its name/summary and date.

    Args:
        meeting_name (str): The name or summary of the meeting to find (case-insensitive partial match)
        date (str): The date to search on (e.g., '2026-01-20' or '2026-01-20T00:00:00')
        calendar_id (str): Calendar ID (defaults to 'primary')

    Returns:
        dict: Meeting details including event_id, or error message
    """
    try:
        service = get_service()

        # Parse the date and create time range for the entire day
        from dateutil import parser as date_parser
        search_date = date_parser.parse(date).date()
        time_min = f"{search_date}T00:00:00Z"
        time_max = f"{search_date}T23:59:59Z"

        # Get all events for that day
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        if not events:
            return {
                "error": f"No meetings found on {search_date}"
            }

        # Search for meetings matching the name (case-insensitive)
        matching_events = []
        meeting_name_lower = meeting_name.lower()

        for event in events:
            summary = event.get('summary', '').lower()
            if meeting_name_lower in summary:
                matching_events.append({
                    'event_id': event['id'],
                    'summary': event.get('summary', 'No Title'),
                    'start': event['start'].get('dateTime', event['start'].get('date')),
                    'end': event['end'].get('dateTime', event['end'].get('date')),
                })

        if not matching_events:
            # List all meetings on that day for reference
            all_meetings = [event.get('summary', 'No Title') for event in events]
            return {
                "error": f"No meeting found with name '{meeting_name}' on {search_date}. "
                        f"Available meetings on this day: {', '.join(all_meetings)}"
            }

        if len(matching_events) == 1:
            return {
                "success": True,
                "meeting": matching_events[0],
                "message": f"Found meeting: {matching_events[0]['summary']}"
            }
        else:
            # Multiple matches - return all for user confirmation
            return {
                "success": True,
                "multiple_matches": True,
                "meetings": matching_events,
                "message": f"Found {len(matching_events)} meetings matching '{meeting_name}'. Please specify which one."
            }

    except Exception as e:
        logger.error(f"Error finding meeting: {e}")
        return {
            "error": f"Failed to find meeting: {str(e)}"
        }

def update_meeting_details():
    pass


def get_service():
    """Handles Google Authentication flow and returns a service object"""
    creds = None
    # The file token.json stores the user's access and refresh tokens
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save the refreshed credentials
                with open(TOKEN_PATH, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                logger.error(f"Failed to refresh credentials: {e}")
                raise ValueError(
                    "Google Calendar credentials expired. Please run 'python src/authenticate.py' to re-authenticate."
                )
        else:
            raise ValueError(
                "Google Calendar not authenticated. Please run 'python src/authenticate.py' first."
            )

    return build('calendar', 'v3', credentials=creds)


@mcp.tool()
def check_availability(start_time: str, end_time: str):
    """
    Check availability. Returns a formatted string of busy times.
    Args:
        start_time: ISO format start (e.g. 2025-11-22T09:00:00Z)
        end_time: ISO format end
    """
    try:
        service = get_service()
        events_result = service.events().list(
            calendarId='primary', timeMin=start_time, timeMax=end_time, 
            singleEvents=True, orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        
        if not events:
            return "No conflicting events found. The time slots are free."

        output = ["Busy times found:"]
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'No Title')
            output.append(f"- {start}: {summary}")
        
        return "\n".join(output)
    except Exception as e:
        return f"Error checking availability: {e}"

@mcp.tool()
def list_upcoming_events(max_results: int = 10):
    """List the next N upcoming events on the primary calendar"""
    try:
        service = get_service()
        now = datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary', timeMin=now,
            maxResults=max_results, singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        if not events:
            return "No upcoming events found."

        output = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            output.append(f"{start} - {event.get('summary', '(No title)')}")
        return "\n".join(output)
    except Exception as e:
        return f"Error listing events: {e}"

if __name__ == "__main__":
    mcp.run() 
