"""
Shared Google OAuth helper used by all Google MCP servers.
Reads credentials and token from paths configured in settings.
"""

import sys
from pathlib import Path

# Allow importing config from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# All scopes needed across all Google MCP servers
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/drive.file",
]


def get_credentials() -> Credentials:
    """
    Load and refresh Google OAuth credentials.
    Token is read from settings.google_token_path.
    Raises ValueError if not authenticated — user must complete OAuth via dashboard.
    """
    token_path = Path(settings.google_token_path)
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(creds.to_json())
            return creds
        except Exception as e:
            raise ValueError(
                f"Google credentials expired and could not be refreshed: {e}. "
                "Please reconnect your Google account via the dashboard."
            )

    raise ValueError(
        "Google account not connected. "
        "Please connect your Google account via the Clubmate dashboard."
    )


def get_service(service_name: str, version: str):
    """Build and return a Google API service client."""
    creds = get_credentials()
    return build(service_name, version, credentials=creds)
