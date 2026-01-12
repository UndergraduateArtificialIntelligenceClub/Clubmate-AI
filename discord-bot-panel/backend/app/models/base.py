"""
Base Model and Mixins
=====================
Common base classes and mixins for all database models.

Design Decisions:
- SQLModel combines SQLAlchemy ORM and Pydantic validation
- All models inherit from BaseModel for consistent ID patterns
- TimestampMixin provides automatic created_at/updated_at
"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field


class TimestampMixin(SQLModel):
    """
    Mixin that adds created_at and updated_at timestamps.
    
    Usage:
        class MyModel(BaseModel, TimestampMixin, table=True):
            ...
    
    Note: updated_at is NOT automatically updated by SQLModel.
    You must set it manually in update operations or use database triggers.
    """
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        description="Record creation timestamp (UTC)"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        nullable=True,
        description="Last update timestamp (UTC)"
    )


class BaseModel(SQLModel):
    """
    Base model providing auto-incrementing primary key.
    
    All table models should inherit from this for consistent ID handling.
    
    Usage:
        class User(BaseModel, table=True):
            username: str
            ...
    """
    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        description="Auto-incrementing primary key"
    )
