"""
Auth Router
===========
Authentication endpoints for Google OAuth.

Endpoints:
- GET /auth/google/connect - Initiate Google OAuth flow
- GET /auth/google/callback - OAuth callback handler
- GET /auth/google/status - Check connection status
- DELETE /auth/google/disconnect - Remove connection
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_session
from app.schemas.auth import GoogleStatusResponse
from app.services.auth_service import AuthService

settings = get_settings()
router = APIRouter()


# ============================================================
# GOOGLE OAUTH
# ============================================================

@router.get("/google/connect")
async def connect_google():
    """
    Initiate Google OAuth flow.
    
    Redirects the user to Google's OAuth consent screen.
    """
    if not settings.google_client_id:
        raise HTTPException(
            status_code=501,
            detail="Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
        )
    
    # Build OAuth URL
    # Scopes for Drive and Gmail access
    scopes = [
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/gmail.send",
        "openid",
        "email",
        "profile",
    ]
    
    oauth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.google_client_id}"
        f"&redirect_uri={settings.google_redirect_uri}"
        "&response_type=code"
        f"&scope={' '.join(scopes)}"
        "&access_type=offline"
        "&prompt=consent"
    )
    
    return RedirectResponse(url=oauth_url)


@router.get("/google/callback")
async def google_callback(
    code: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Handle Google OAuth callback.
    
    Exchanges authorization code for tokens and stores them.
    """
    import httpx
    
    # Exchange code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail="Failed to exchange authorization code"
            )
        
        token_data = response.json()
    
    # For demo purposes, using a fixed user_id
    # In production, get this from session/auth
    user_id = 1
    
    from datetime import datetime, timezone, timedelta
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600))
    
    await AuthService.save_google_token(
        session,
        user_id=user_id,
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        expires_at=expires_at,
        scope=token_data.get("scope"),
    )
    
    # Redirect back to frontend with success message
    return RedirectResponse(url="http://localhost:5173/google?status=success")


@router.get("/google/status", response_model=GoogleStatusResponse)
async def get_google_status(
    session: AsyncSession = Depends(get_session),
):
    """
    Check if Google account is connected.
    
    Returns connection status and connected email if available.
    """
    # For demo purposes, using a fixed user_id
    # In production, get this from session/auth
    user_id = 1
    
    is_connected = await AuthService.is_google_connected(session, user_id)
    
    return GoogleStatusResponse(
        is_connected=is_connected,
        email=None,  # Could fetch from Google userinfo API
    )


@router.delete("/google/disconnect", status_code=204)
async def disconnect_google(
    session: AsyncSession = Depends(get_session),
):
    """
    Disconnect Google account.
    
    Removes stored OAuth tokens.
    """
    # For demo purposes, using a fixed user_id
    # In production, get this from session/auth
    user_id = 1
    
    disconnected = await AuthService.disconnect_google(session, user_id)
    if not disconnected:
        raise HTTPException(status_code=404, detail="Google account not connected")
    
    return None
