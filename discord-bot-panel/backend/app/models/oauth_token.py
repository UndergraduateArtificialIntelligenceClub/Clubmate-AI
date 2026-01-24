"""
OAuth Token Model
=================
Secure storage for OAuth tokens (Google, etc.).

Tokens are encrypted at rest just like API keys.
Refresh tokens allow the application to maintain
long-term access without re-authentication.
"""

from typing import Optional
from datetime import datetime
from sqlmodel import Field

from app.models.base import BaseModel, TimestampMixin


class OAuthToken(BaseModel, TimestampMixin, table=True):
    """
    Encrypted OAuth token storage.
    
    Stores access and refresh tokens for third-party OAuth providers.
    Currently used for Google (Drive/Gmail integration).
    """
    __tablename__ = "oauth_tokens"
    
    # Which user this token belongs to
    user_id: int = Field(
        foreign_key="users.id",
        index=True,
        description="User who authorized this OAuth connection"
    )
    
    # OAuth provider (for future multi-provider support)
    provider: str = Field(
        max_length=32,
        index=True,
        default="google",
        description="OAuth provider (e.g., 'google')"
    )
    
    # Encrypted tokens
    access_token_encrypted: str = Field(
        description="Fernet-encrypted access token"
    )
    refresh_token_encrypted: Optional[str] = Field(
        default=None,
        description="Fernet-encrypted refresh token"
    )
    
    # Token metadata
    token_type: str = Field(
        max_length=32,
        default="Bearer",
        description="Token type (usually 'Bearer')"
    )
    expires_at: Optional[datetime] = Field(
        default=None,
        description="When the access token expires"
    )
    
    # Scope information
    scope: Optional[str] = Field(
        default=None,
        max_length=512,
        description="OAuth scopes granted"
    )
    
    # Store which specific account was connected (e.g. email)
    account_email: Optional[str] = Field(
        default=None,
        max_length=255,
        description="The email/identifier of the connected account"
    )
    
    class Config:
        # Composite index for efficient lookups
        table_args = {
            "indexes": [
                {"name": "idx_oauth_user_provider", "fields": ["user_id", "provider"]}
            ]
        }
