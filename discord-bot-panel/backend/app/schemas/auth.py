"""
Auth Schemas
============
Response schemas for authentication operations.
"""

from pydantic import BaseModel


class GoogleStatusResponse(BaseModel):
    """Google OAuth connection status."""
    is_connected: bool
    email: str | None = None  # Connected Google account email
