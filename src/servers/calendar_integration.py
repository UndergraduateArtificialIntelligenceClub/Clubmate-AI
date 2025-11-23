from fastmcp import FastMCP
from datetime import datetime, timedelta
import os
from typing import List  # <--- ADD THIS IMPORT

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

mcp = FastMCP("Google Calendar MCP")

SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
]

def get_service():
    """Handles Google Authentication flow and returns a service object"""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

# --- UPDATED FUNCTION SIGNATURE BELOW ---
@mcp.tool()
def schedule_meeting(
    id: str = "primary", 
    start_time: str = None, 
    end_time: str = None, 
    attendees: List[str] = [],  # <--- CHANGED from 'list' to 'List[str]'
    summary: str = "Meeting"
):
    """
    Schedule a meeting. Times must be in ISO format (e.g., 2023-11-22T15:00:00).
    """
    try:
        service = get_service()
        event = {
            'summary': summary,
            'start': {'dateTime': start_time, 'timeZone': 'Canada/Pacific'},
            'end': {'dateTime': end_time, 'timeZone': 'Canada/Pacific'},
            'attendees': [{'email': email} for email in attendees],
        }
        created_event = service.events().insert(calendarId=id, body=event).execute()
        return f"Meeting scheduled: {created_event.get('htmlLink')}"
    except Exception as e:
        return f"Error scheduling meeting: {e}"

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
