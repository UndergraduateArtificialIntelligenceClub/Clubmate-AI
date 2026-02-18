"""
Google OAuth flow endpoints.
The dashboard redirects here to connect the club's Google account.
On success, stores token.json to the configured path.
"""

import json
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from api.auth import verify_discord_admin
from config import settings, PROJECT_ROOT

router = APIRouter(prefix="/google", tags=["google"])

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/drive.file",
]


def _oauth_redirect_uri(request: Request | None) -> str:
    """
    Build a callback URI that matches the externally reachable API host.
    Falls back to localhost when API_HOST is 0.0.0.0/::.
    """
    if request is not None:
        # Prefer the host/scheme seen by the incoming request.
        base = str(request.base_url).rstrip("/")
        return f"{base}/google/callback"

    host = settings.api_host.strip()
    if host in {"", "0.0.0.0", "::"}:
        host = "localhost"
    return f"http://{host}:{settings.api_port}/google/callback"


class CredentialsUpload(BaseModel):
    credentials_json: str  # Raw JSON string from Google Cloud Console OAuth client


@router.get("/status")
async def google_status(_user: dict = Depends(verify_discord_admin)):
    """Check if Google account is connected."""
    token_path = Path(settings.google_token_path)
    connected = token_path.exists()

    account_email = None
    if connected:
        try:
            token_data = json.loads(token_path.read_text())
            # Email is not stored in token.json — try to get it via API
            from mcp_servers.google_auth import get_credentials
            creds = get_credentials()
            import httpx
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {creds.token}"},
                )
                if res.status_code == 200:
                    account_email = res.json().get("email")
        except Exception:
            pass

    return {"connected": connected, "account_email": account_email}


@router.post("/credentials")
async def upload_credentials(
    body: CredentialsUpload,
    _user: dict = Depends(verify_discord_admin),
):
    """
    Save Google OAuth credentials JSON (downloaded from Google Cloud Console).
    This is step 1 — after uploading, call /google/auth to start the OAuth flow.
    """
    try:
        creds_data = json.loads(body.credentials_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in credentials_json")

    creds_path = Path(settings.google_credentials_path)
    creds_path.parent.mkdir(parents=True, exist_ok=True)
    creds_path.write_text(json.dumps(creds_data, indent=2))

    return {"message": "Credentials saved. Now call /google/auth to connect your Google account."}


@router.get("/auth")
async def start_oauth(_user: dict = Depends(verify_discord_admin), request: Request = None):
    """
    Start the Google OAuth flow.
    Returns the authorization URL for the dashboard to redirect to.
    """
    creds_path = Path(settings.google_credentials_path)
    if not creds_path.exists():
        raise HTTPException(
            status_code=400,
            detail="Google credentials not uploaded. POST to /google/credentials first.",
        )

    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_secrets_file(
        str(creds_path),
        scopes=SCOPES,
        redirect_uri=_oauth_redirect_uri(request),
    )
    auth_url, _ = flow.authorization_url(access_type="offline", include_granted_scopes="true")

    return {"auth_url": auth_url}


@router.get("/callback")
async def oauth_callback(code: str, request: Request):
    """
    Google OAuth callback — exchanges code for tokens and saves to disk.
    The dashboard should redirect here after user approves Google access.
    """
    creds_path = Path(settings.google_credentials_path)
    if not creds_path.exists():
        raise HTTPException(status_code=400, detail="Credentials file missing")

    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_secrets_file(
        str(creds_path),
        scopes=SCOPES,
        redirect_uri=_oauth_redirect_uri(request),
    )
    flow.fetch_token(code=code)

    token_path = Path(settings.google_token_path)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(flow.credentials.to_json())

    return {"message": "Google account connected successfully. You can close this tab."}


@router.delete("/disconnect")
async def disconnect_google(_user: dict = Depends(verify_discord_admin)):
    """Remove stored Google token, disconnecting the Google account."""
    token_path = Path(settings.google_token_path)
    if token_path.exists():
        token_path.unlink()
    return {"message": "Google account disconnected."}
