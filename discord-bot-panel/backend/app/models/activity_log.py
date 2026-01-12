"""
Activity Log Model
==================
Audit trail for user actions in the system.

Used for:
- Dashboard activity feed
- Security auditing
- Debugging issues
"""

from datetime import datetime, timezone
from typing import Optional, Any

from sqlmodel import Field, Column, JSON

from app.models.base import BaseModel


class ActivityLog(BaseModel, table=True):
    """
    Audit log entry for user actions.
    
    Tracks what actions were performed, by whom, and the outcome.
    Details field stores action-specific context as JSON.
    """
    __tablename__ = "activity_logs"
    
    # Who performed the action (nullable for system actions)
    user_id: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
        index=True,
        description="User who performed the action"
    )
    
    # What action was performed
    action: str = Field(
        max_length=50,
        index=True,
        description="Action type (e.g., 'create_contact', 'upload_file')"
    )
    
    # Action-specific details
    # Example: {"contact_id": 123, "contact_name": "John Doe"}
    details: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
        description="JSON details about the action"
    )
    
    # Outcome
    status: str = Field(
        max_length=20,
        index=True,
        description="Outcome: 'success', 'failure', 'pending'"
    )
    
    # When
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
        description="When the action occurred"
    )

