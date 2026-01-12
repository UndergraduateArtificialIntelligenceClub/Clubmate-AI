"""
API Key Model
=============
Secure storage for third-party API keys (OpenAI, etc.).

Security Architecture:
- Keys are encrypted at rest using Fernet symmetric encryption
- A hash of the key is stored for uniqueness checks
- The actual key value is NEVER returned after creation
- Only a masked version (first/last 4 chars) is shown in responses
"""

from typing import Optional
from datetime import datetime
from sqlmodel import Field

from app.models.base import BaseModel, TimestampMixin


class APIKey(BaseModel, TimestampMixin, table=True):
    """
    Encrypted API key storage.
    
    Used to store third-party service credentials securely.
    Keys are encrypted before storage and never returned in plaintext.
    """
    __tablename__ = "api_keys"
    
    # Descriptive name for the key
    name: str = Field(
        max_length=100,
        description="Service name (e.g., 'OpenAI', 'Discord Bot Token')"
    )
    
    # Encrypted key value (Fernet encrypted)
    encrypted_value: str = Field(
        description="Fernet-encrypted API key value"
    )
    
    # Hash for uniqueness check (SHA-256)
    # Prevents storing the same key twice
    key_hash: str = Field(
        unique=True,
        max_length=64,
        index=True,
        description="SHA-256 hash of the original key for deduplication"
    )
    
    # Masked display version (e.g., "sk-ab...xy12")
    masked: str = Field(
        max_length=32,
        description="Masked version for display"
    )
    
    # Status tracking
    is_active: bool = Field(
        default=True,
        index=True,
        description="Whether the key is active/usable"
    )
    
    # Usage tracking
    last_used_at: Optional[datetime] = Field(
        default=None,
        description="Last time the key was accessed"
    )
    
    # Ownership
    user_id: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
        index=True,
        description="User who created this key"
    )
