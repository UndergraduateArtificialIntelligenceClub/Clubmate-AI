from fastmcp import FastMCP

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
]

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

def schedule_meeting(
        id: str, 
        start_time: str, 
        end_time: str, 
        attendees: list, 
        summary: str
        ):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    service = build('calendar', 'v3', credentials=creds)

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
        'attendees': [{'email': email} for email in attendees],
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
    print(f"Meeting '{summary}' scheduled from {start_time} to {end_time} with attendees {attendees}")
    link = event.get('htmlLink', 'No link available')
    print(f"Link: {link}")

def cancel_meeting():
    pass

def reschedule_meeting(id: str, event_id: str, new_start_time: str, new_end_time: str):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    service = build('calendar', 'v3', credentials=creds)

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
    print(f"Meeting '{event['summary']}' rescheduled from {event['start']['dateTime']} to {event['end']['dateTime']}")
    print(f"Link: {link}")

def add_invites():
    pass

def check_availability():
    pass

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