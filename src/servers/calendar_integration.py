from fastmcp import FastMCP
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


import os

mcp = FastMCP("Google Calendar MCP")

# SCOPES define what we can do with the Google Calendar API
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
]

@mcp.tool()
def schedule_meeting(
        id: str,
        start_time: str,
        end_time: str,
        attendees: list,
        summary: str
        ):
    """
    Schedule a meeting on Google Calendar.
    Args:
        id (str): Calendar ID
        start_time (str): Start time format
        end_time (str): End time format
        attendees (list): List of attendee email addresses
        summary (str): Summary or title of the meeting
    """
    service = get_service()

    event = {
        'summary': summary,
        'start': {
            'dateTime': start_time,
            'timeZone': 'Canada/Pacific',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'Canada/Pacific',
        },
        'attendees': [{'email': email} for email in attendees], # List of dicts with 'email' keys
        'reminders': {
            'useDefault': False,
            'overrides': [
                # Change this later so its customizable, just add another field
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ]
        }
    }

    service.events().insert(calendarId=id, body=event).execute()
    link = event.get('htmlLink', 'No link available')
    return {"link": link, "message": f"Meeting '{summary}' scheduled from {start_time} to {end_time} with attendees {attendees}"}

def cancel_meeting():
    pass

@mcp.tool()
def reschedule_meeting(id: str, event_id: str, new_start_time: str, new_end_time: str):
    """
    Reschedule a meeting to a new time.
    Args:
        id (str): Calendar ID
        event_id (str): Event ID of the meeting to be rescheduled
        new_start_time (str): New start time in RFC3339 format
        new_end_time (str): New end time in RFC3339 format
    """
    service = get_service()

    event = service.events().get(calendarId=id, eventId=event_id).execute()
    event['start'] = {
        'dateTime': new_start_time,
        'timeZone': 'Canada/Pacific',
    }
    event['end'] = {
        'dateTime': new_end_time,
        'timeZone': 'Canada/Pacific',
    }

    event = service.events().update(calendarId=id, eventId=event_id, body=event).execute()
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
    
    return "\n".join(result)

@mcp.tool()
def get_meetings():
    pass

def update_meeting_details():
    pass


def get_service():
    """
    Handles Google Authentication flow and returns a service object for Google Calendar API
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # This opens your browser to ask for permission
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

if __name__ == "__main__":
    mcp.run()
