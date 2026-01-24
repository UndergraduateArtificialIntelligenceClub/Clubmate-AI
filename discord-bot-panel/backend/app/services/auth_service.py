"""
Auth Service
============
Authentication and OAuth handling.

Currently supports:
- Discord OAuth for Login
- Google OAuth for Drive/Gmail integration
- JWT Token Generation and Verification
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from jose import jwt, JWTError
import httpx

from app.config import get_settings
from app.models import User, OAuthToken, ActivityLog
from app.utils.security import SecurityUtils

settings = get_settings()

class AuthService:
    """
    Service for authentication and OAuth token management.
    """
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify a JWT token."""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
            return payload
        except JWTError:
            return None

    @staticmethod
    async def get_user_by_discord_id(session: AsyncSession, discord_id: str) -> Optional[User]:
        """Get user by Discord ID."""
        query = select(User).where(User.discord_id == discord_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by Database ID."""
        return await session.get(User, user_id)

    @staticmethod
    async def discord_login(session: AsyncSession, code: str) -> Dict[str, Any]:
        """
        Handle Discord OAuth Login.
        
        1. Exchange code for access token
        2. Get user info from Discord
        3. Find or create User in DB
        4. Generate JWT
        """
        if not settings.discord_client_id or not settings.discord_client_secret:
             raise HTTPException(status_code=501, detail="Discord OAuth not configured")

        # 1. Exchange code for token
        async with httpx.AsyncClient() as client:
            data = {
                'client_id': settings.discord_client_id,
                'client_secret': settings.discord_client_secret,
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': settings.discord_redirect_uri,
            }
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            r = await client.post('https://discord.com/api/oauth2/token', data=data, headers=headers)
            
            if r.status_code != 200:
                raise HTTPException(status_code=400, detail="Invalid Discord Auth Code")
            
            token_response = r.json()
            access_token = token_response['access_token']

            # 2. Get user info
            user_r = await client.get('https://discord.com/api/users/@me', headers={
                'Authorization': f'Bearer {access_token}'
            })
            
            if user_r.status_code != 200:
                 raise HTTPException(status_code=400, detail="Failed to fetch Discord user")
            
            discord_user = user_r.json()
            
        # 3. Find or Create User
        user = await AuthService.get_user_by_discord_id(session, discord_user['id'])
        
        if not user:
            # Create new user
            user = User(
                discord_id=discord_user['id'],
                username=discord_user['username'],
                email=discord_user.get('email'),
                avatar_url=f"https://cdn.discordapp.com/avatars/{discord_user['id']}/{discord_user['avatar']}.png" if discord_user.get('avatar') else None,
                role=1 # Default to Member
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            # Update info
            user.username = discord_user['username']
            user.email = discord_user.get('email')
            user.avatar_url = f"https://cdn.discordapp.com/avatars/{discord_user['id']}/{discord_user['avatar']}.png" if discord_user.get('avatar') else None
            session.add(user)
            await session.commit()
            await session.refresh(user)

        # 4. Generate JWT
        access_token_jwt = AuthService.create_access_token(data={"sub": str(user.id)})
        
        return {
            "access_token": access_token_jwt,
            "token_type": "bearer",
            "user": user
        }

    # ... (Google methods remain largely the same, but using user_id)
    
    @staticmethod
    async def get_google_token(
        session: AsyncSession,
        user_id: int,
    ) -> Optional[OAuthToken]:
        """Get Google OAuth token for a user."""
        query = select(OAuthToken).where(
            OAuthToken.user_id == user_id,
            OAuthToken.provider == "google"
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def is_google_connected(
        session: AsyncSession,
        user_id: int,
    ) -> bool:
        """Check if user has a valid Google OAuth connection."""
        token = await AuthService.get_google_token(session, user_id)
        if not token:
            return False
        
        # Check if token is expired
        if token.expires_at:
            # Make sure we compare timezone-aware datetimes
            expires = token.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires < datetime.now(timezone.utc):
                return False
        
        return True
    
    @staticmethod
    async def save_google_token(
        session: AsyncSession,
        user_id: int,
        access_token: str,
        refresh_token: Optional[str],
        expires_at: Optional[datetime],
        scope: Optional[str] = None,
        account_email: Optional[str] = None,
    ) -> OAuthToken:
        """
        Save or update Google OAuth tokens for a user.
        
        Tokens are encrypted before storage.
        """
        # Check for existing token
        existing = await AuthService.get_google_token(session, user_id)
        
        # Encrypt tokens
        access_token_encrypted = SecurityUtils.encrypt(access_token)
        refresh_token_encrypted = SecurityUtils.encrypt(refresh_token) if refresh_token else None
        
        if existing:
            # Update existing token
            existing.access_token_encrypted = access_token_encrypted
            existing.refresh_token_encrypted = refresh_token_encrypted
            existing.expires_at = expires_at
            existing.scope = scope
            existing.account_email = account_email
            existing.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(existing)
            return existing
        else:
            # Create new token
            token = OAuthToken(
                user_id=user_id,
                provider="google",
                access_token_encrypted=access_token_encrypted,
                refresh_token_encrypted=refresh_token_encrypted,
                expires_at=expires_at,
                scope=scope,
                account_email=account_email,
            )
            session.add(token)
            await session.commit()
            await session.refresh(token)
            
            # Log the action
            log = ActivityLog(
                user_id=user_id,
                action="connect_google",
                details={"provider": "google"},
                status="success",
            )
            session.add(log)
            await session.commit()
            
            return token
    
    @staticmethod
    async def disconnect_google(
        session: AsyncSession,
        user_id: int,
    ) -> bool:
        """
        Remove Google OAuth connection for a user.
        
        Returns True if disconnected, False if not connected.
        """
        token = await AuthService.get_google_token(session, user_id)
        if not token:
            return False
        
        await session.delete(token)
        await session.commit()
        
        # Log the action
        log = ActivityLog(
            user_id=user_id,
            action="disconnect_google",
            details={"provider": "google"},
            status="success",
        )
        session.add(log)
        await session.commit()
        
        return True
    
    @staticmethod
    async def get_decrypted_google_token(
        session: AsyncSession,
        user_id: int,
    ) -> Optional[str]:
        """
        Get decrypted Google access token.
        
        Used when actually calling Google APIs.
        """
        token = await AuthService.get_google_token(session, user_id)
        if not token:
            return None
        
        return SecurityUtils.decrypt(token.access_token_encrypted)
