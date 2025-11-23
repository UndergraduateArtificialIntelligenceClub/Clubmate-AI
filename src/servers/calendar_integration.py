from fastmcp import FastMCP

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
]

# TODO: Add documentation

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

def get_meetings():
    pass

def update_meeting_details():
    pass
