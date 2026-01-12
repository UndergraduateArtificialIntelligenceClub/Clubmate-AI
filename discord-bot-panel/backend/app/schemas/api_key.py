"""
API Key Schemas
===============
Request/response schemas for API key operations.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class APIKeyCreate(BaseModel):
    """Schema for creating a new API key."""
    name: str = Field(..., min_length=1, max_length=100, description="Service name")
    value: str = Field(..., min_length=1, description="The API key value (will be encrypted)")


class APIKeyResponse(BaseModel):
    """
    Schema for API key in responses.
    
    Note: The actual key value is NEVER returned.
    Only the masked version is shown.
    """
    id: int
    name: str
    masked: str  # e.g., "sk-ab...xy12"
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class APIKeyListResponse(BaseModel):
    """List of API keys."""
    items: List[APIKeyResponse]
    total: int
