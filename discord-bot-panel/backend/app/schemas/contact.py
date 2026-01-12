"""
Contact Schemas
===============
Request/response schemas for contact operations.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field


class ContactBase(BaseModel):
    """Base schema with common contact fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Contact name")
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, max_length=32, description="Phone number")
    discord_id: Optional[str] = Field(None, max_length=32, description="Discord user ID")
    discord_username: Optional[str] = Field(None, max_length=32, description="Discord username")
    notes: Optional[str] = Field(None, description="Additional notes")
    tags: List[str] = Field(default=[], description="Tags for categorization")


class ContactCreate(ContactBase):
    """Schema for creating a new contact."""
    pass


class ContactUpdate(BaseModel):
    """Schema for updating a contact (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=32)
    discord_id: Optional[str] = Field(None, max_length=32)
    discord_username: Optional[str] = Field(None, max_length=32)
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class ContactResponse(ContactBase):
    """Schema for contact in API responses."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # Enable ORM mode


class ContactListResponse(BaseModel):
    """Paginated list of contacts."""
    items: List[ContactResponse]
    total: int
    page: int
    per_page: int
