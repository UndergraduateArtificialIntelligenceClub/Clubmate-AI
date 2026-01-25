"""
Auth Router
===========
Authentication endpoints for Discord (Login) and Google (Linking).

Endpoints:
- POST /auth/discord/login - Initiate Discord OAuth flow
- GET /auth/discord/callback - OAuth callback handler & Login
- GET /auth/google/connect - Initiate Google OAuth flow (Account Linking)
- GET /auth/google/callback - OAuth callback handler (Account Linking)
- GET /auth/me - Get current user info
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Cookie, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.config import get_settings
from app.database import get_session
from app.schemas.auth import GoogleStatusResponse
from app.services.auth_service import AuthService
from app.models import User

settings = get_settings()
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency to get current user
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session)
) -> User:
    payload = AuthService.verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user = await AuthService.get_user_by_id(session, int(user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# ============================================================
# DISCORD OAUTH (LOGIN)
# ============================================================

# In-memory store for pending logins (state -> token_data)
# For a production app with multiple replicas, use Redis.
pending_logins = {}

@router.get("/discord/login")
async def login_discord(
    user_redirect: bool = False # If True, return JSON with URL for system browser
):
    """
    Initiate Discord OAuth flow for login.
    """
    if not settings.discord_client_id or not settings.discord_client_secret:
        # If running locally without OAuth, we can offer a "bypass" or just error
        # In a real local app, we might check if environment is "development"
        raise HTTPException(
            status_code=501, 
            detail="Discord OAuth not configured. Please provide Client ID and Secret in Settings."
        )
        
    logout_url = "https://discord.com/api/oauth2/authorize"
    # To read/write messages, we typically need the bot to be added to the server.
    # We add 'bot' scope and permissions=68608 (Read Messages, Send Messages).
    # 'applications.commands' is also useful for slash commands.
    scope = "identify email bot applications.commands"
    permissions = "68608" # Read Messages + Send Messages
    
    # Generate a random state for security and polling
    import uuid
    state = str(uuid.uuid4())
    
    # Prepare pending entry
    if user_redirect:
        pending_logins[state] = {"status": "pending"}

    oauth_url = (
        f"{logout_url}?"
        f"client_id={settings.discord_client_id}"
        f"&redirect_uri={settings.discord_redirect_uri}"
        "&response_type=code"
        f"&scope={scope}"
        f"&permissions={permissions}"
        f"&state={state}"
    )
    
    if user_redirect:
        return {"url": oauth_url, "state": state}
    
    return RedirectResponse(url=oauth_url)

@router.get("/discord/callback")
async def discord_callback(
    code: str,
    state: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Handle Discord OAuth callback.
    """
    try:
        auth_data = await AuthService.discord_login(session, code)
        
        # If this state is being tracked (system browser login), update the store
        if state in pending_logins:
            pending_logins[state] = {
                "status": "complete",
                "auth_data": auth_data
            }
            # Return a simple success page for the external browser
            html_content = """
            <html>
                <head><title>Login Successful</title></head>
                <body style="background-color: #1a1b1e; color: #fff; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh;">
                    <div style="text-align: center;">
                        <h1 style="color: #5865F2;">Login Successful!</h1>
                        <p>You can close this window and return to the application.</p>
                        <script>window.close();</script>
                    </div>
                </body>
            </html>
            """
            return Response(content=html_content, media_type="text/html")

        # Standard flow (webview redirect)
        frontend_url = f"http://localhost:5173/auth/callback?token={auth_data['access_token']}"
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        print(f"Login error: {e}")
        if state in pending_logins:
             pending_logins[state] = {"status": "error", "message": str(e)}
             return Response(content="Login failed. Check app for details.", media_type="text/plain")

        return RedirectResponse(url="http://localhost:5173/login?error=auth_failed")

@router.get("/discord/poll")
async def poll_discord_login(state: str):
    """
    Poll checking if external login is complete.
    """
    if state not in pending_logins:
        raise HTTPException(status_code=404, detail="Invalid or expired session")
    
    data = pending_logins[state]
    
    if data["status"] == "pending":
        return {"status": "pending"}
    
    if data["status"] == "complete":
        # Clean up
        del pending_logins[state]
        return {"status": "complete", "token": data["auth_data"]["access_token"]}
        
    if data["status"] == "error":
        del pending_logins[state]
        raise HTTPException(status_code=400, detail=data.get("message", "Login failed"))
    
    return {"status": "unknown"}

@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current logged in user."""
    return current_user

# ============================================================
# LOCAL DEV BYPASS
# ============================================================
@router.post("/dev-login")
async def dev_login(
    session: AsyncSession = Depends(get_session)
):
    """
    Bypass OAuth for local development.
    Creates a 'Developer' user and returns a token.
    """
    # Only allow if Client Secret is missing (indicating local mode) 
    # OR if explicitly in development mode
    is_local_mode = not settings.discord_client_secret
    if settings.environment != "development" and not is_local_mode:
        raise HTTPException(
            status_code=403, 
            detail="Dev login only available in development mode or when OAuth is unconfigured."
        )
        
    # Check if 'Developer' user exists
    user = await AuthService.get_user_by_discord_id(session, "developer")
    
    if not user:
        # Create 'Developer' user
        user = User(
            discord_id="developer",
            username="Developer",
            email="dev@local",
            role=2, # Admin
            avatar_url="https://ui-avatars.com/api/?name=Developer&background=random"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    
    # Generate token
    access_token_jwt = AuthService.create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token_jwt,
        "token_type": "bearer",
        "user": user
    }

# ============================================================
# GOOGLE OAUTH (ACCOUNT LINKING)
# ============================================================

@router.get("/google/connect")
async def connect_google(
    current_user: User = Depends(get_current_user), # Requires login
):
    """
    Initiate Google OAuth flow for account linking.
    """
    if not settings.google_client_id:
        raise HTTPException(
            status_code=501,
            detail="Google OAuth not configured."
        )
    
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
        f"&state={current_user.id}"
    )
    
    return {"url": oauth_url}


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str = None,
    session: AsyncSession = Depends(get_session),
):
    """
    Handle Google OAuth callback.
    """
    if not state:
        raise HTTPException(status_code=400, detail="Missing state parameter")
        
    try:
        user_id = int(state)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

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
            print(response.text)
            return RedirectResponse(url="http://localhost:5173/google?error=auth_failed")
        
        token_data = response.json()
    
    # Fetch Google user info to get the email
    async with httpx.AsyncClient() as client:
        userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        userinfo_response = await client.get(
            userinfo_url,
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )
        userinfo = userinfo_response.json() if userinfo_response.status_code == 200 else {}
        account_email = userinfo.get("email")

    from datetime import datetime, timezone, timedelta
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600))
    
    await AuthService.save_google_token(
        session,
        user_id=user_id,
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        expires_at=expires_at,
        scope=token_data.get("scope"),
        account_email=account_email,
    )
    
    return RedirectResponse(url="http://localhost:5173/google?status=success")


@router.get("/google/status", response_model=GoogleStatusResponse)
async def get_google_status(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Check if Google account is connected.
    """
    is_connected = await AuthService.is_google_connected(session, current_user.id)
    
    # Get email from token if available
    email = None
    if is_connected:
        token = await AuthService.get_google_token(session, current_user.id)
        if token:
            email = token.account_email or current_user.email  # Fallback only if email unknown
    
    return GoogleStatusResponse(
        is_connected=is_connected,
        email=email, 
    )

@router.delete("/google/disconnect", status_code=204)
async def disconnect_google(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Disconnect Google account.
    """
    disconnected = await AuthService.disconnect_google(session, current_user.id)
    if not disconnected:
        raise HTTPException(status_code=404, detail="Google account not connected")
    
    return None
