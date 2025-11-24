from fastmcp import FastMCP
from datetime import datetime, timedelta
import os
from typing import List  

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from typing import Optional, List,Union

from pathlib import Path

# Get the directory where credentials are stored (right now its in Clu)
SCRIPT_DIR = Path(__file__).parent.parent  # Points to src/
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

    # ---- FIX THE TIMEZONE BUG HERE ----
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

def cancel_meeting():
    pass

@mcp.tool()
def reschedule_meeting(
        id: str,
        new_start_time: str,
        new_end_time: str,
        event_id: Optional[str] = 'primary',
        timezone: Optional[str] = "America/Edmonton",
        ):
    """
    Reschedule a meeting to a new time.
    Args:
        id (str): Calendar ID
        new_start_time (str): New start time
        new_end_time (str): New end time
        event_id (str): Event ID of the meeting to be rescheduled (defaults to 'primary')
        timezone (str): timezone name (e.g., 'America/Edmonton', 'America/Vancouver'). Defaults to Mountain Time.
    """
    service = get_service()

    event = service.events().get(calendarId=id, eventId=event_id).execute()
    event['start'] = {
        'dateTime': new_start_time,
        'timeZone': timezone,
    }
    event['end'] = {
        'dateTime': new_end_time,
        'timeZone': timezone,
    }

    event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
    link = event.get('htmlLink', 'No link available')
    # return JsonResponse
    return {"link": link, "message": f"Meeting rescheduled to {new_start_time} - {new_end_time}"}

def add_invites():
    pass

@mcp.tool()
def check_availability(start_time: str, end_time: str):
    """
    Check availability of the time slots.
    Query which time slots are free and available between the given start_time and end_time.
    """
    service = get_service()
    # Call the Calendar API
    events_result = service.events().list(calendarId='primary', timeMin=start_time,
                                          timeMax=end_time, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    
    # Parse start and end dates
    start_date = datetime.fromisoformat(start_time.replace('Z', '+00:00')).date()
    end_date = datetime.fromisoformat(end_time.replace('Z', '+00:00')).date()
    
    # Build result string
    result = {}
    current_date = start_date
    
    while current_date <= end_date:
        day_str = current_date.isoformat()
        # Check and list events for the current day
        day_events = [event for event in events if event['start'].get('dateTime', event['start'].get('date')).startswith(day_str)]
        
        # If no events, the day is marked as "free"
        if not day_events:
            result[day_str] = "free"
        else:
            # For each day that has events,list the events
            # First list out the times that are busy then the events occupying those times
            # Day is marked as "busy"
            busy_times = []
            for event in day_events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                busy_times.append(f"{start} to {end}: {event.get('summary', 'No Title')}")
            result[day_str] = "busy"
            result[day_str + "_details"] = "\n".join(busy_times)

        current_date += timedelta(days=1)

    # Convert result dict to formatted string
    output = []
    for key, value in result.items():
        output.append(f"{key}: {value}")
    return "\n".join(output)

@mcp.tool()
def get_meetings():
    pass

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
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

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
