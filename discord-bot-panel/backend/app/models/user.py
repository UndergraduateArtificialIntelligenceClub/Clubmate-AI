"""
User Model
==========
Admin users who can access the bot panel.
Authenticated via Discord OAuth.

This is separate from Contacts - Users are admin accounts,
while Contacts are the people the bot interacts with.
"""

from typing import Optional
from sqlmodel import Field, Relationship

from app.models.base import BaseModel, TimestampMixin


class User(BaseModel, TimestampMixin, table=True):
    """
    Admin user with panel access.
    
    Authenticated via Discord OAuth, with role-based permissions.
    
    Roles:
        0 = Admin (full access)
        1 = Member (limited access)
        2 = Viewer (read-only)
    """
    __tablename__ = "users"
    
    # Discord OAuth fields
    discord_id: str = Field(
        unique=True, 
        index=True,
        max_length=32,
        description="Discord user ID (snowflake)"
    )
    username: str = Field(
        max_length=32,
        description="Discord username"
    )
    email: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Email from Discord OAuth"
    )
    avatar_url: Optional[str] = Field(
        default=None,
        max_length=512,
        description="Discord avatar URL"
    )
    
    # Authorization
    role: int = Field(
        default=1,
        index=True,
        description="User role: 0=Admin, 1=Member, 2=Viewer"
    )
    is_active: bool = Field(
        default=True,
        description="Whether user can access the panel"
    )
    
    # Relationships (populated by SQLModel when queried)
    # contacts: list["Contact"] = Relationship(back_populates="created_by_user")
    # files: list["File"] = Relationship(back_populates="uploaded_by_user")
    # api_keys: list["APIKey"] = Relationship(back_populates="user")
    # activity_logs: list["ActivityLog"] = Relationship(back_populates="user")
    
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.role == 0
    
    def can_write(self) -> bool:
        """Check if user can create/update/delete resources."""
        return self.role in (0, 1)
