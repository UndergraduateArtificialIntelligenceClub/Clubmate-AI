"""
Contact Model
=============
General contact storage for people the bot/organization interacts with.

This stores contact information like email, phone, Discord, etc.
NOT the same as Users (who are admin accounts).
"""

from typing import Optional, List
from sqlmodel import Field, Column, JSON

from app.models.base import BaseModel, TimestampMixin


class Contact(BaseModel, TimestampMixin, table=True):
    """
    General contact record for individuals.
    
    Can store multiple contact methods and notes.
    Tags can be used for categorization/filtering.
    """
    __tablename__ = "contacts"
    
    # Core contact info
    name: str = Field(
        max_length=255,
        description="Contact's full name"
    )
    
    # Contact methods (all optional)
    email: Optional[str] = Field(
        default=None,
        max_length=255,
        index=True,
        description="Email address"
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=32,
        description="Phone number"
    )
    
    # Discord integration
    discord_id: Optional[str] = Field(
        default=None,
        max_length=32,
        index=True,
        description="Discord user ID (snowflake)"
    )
    discord_username: Optional[str] = Field(
        default=None,
        max_length=32,
        description="Discord username"
    )
    
    # Additional info
    notes: Optional[str] = Field(
        default=None,
        description="Free-form notes about the contact"
    )
    
    # Tags for categorization (stored as JSON array)
    # Example: ["member", "sponsor", "speaker"]
    tags: List[str] = Field(
        default=[],
        sa_column=Column(JSON, nullable=False, server_default="[]"),
        description="Tags for filtering and categorization"
    )
    
    # Audit trail
    created_by: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
        description="User who created this contact"
    )
