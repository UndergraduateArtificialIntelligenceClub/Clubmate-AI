"""
Auth Service
============
Authentication and OAuth handling.

Currently supports:
- Google OAuth for Drive/Gmail integration
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, OAuthToken, ActivityLog
from app.utils.security import SecurityUtils


class AuthService:
    """
    Service for authentication and OAuth token management.
    """
    
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
        if token.expires_at and token.expires_at < datetime.now(timezone.utc):
            # Token expired - could implement refresh here
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
