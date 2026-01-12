"""
Stats Schemas
=============
Response schemas for dashboard statistics.
"""

from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel


class StatsResponse(BaseModel):
    """Dashboard statistics."""
    total_contacts: int
    total_files: int
    total_api_keys: int
    active_api_keys: int
    

class LogResponse(BaseModel):
    """Single activity log entry."""
    id: int
    action: str
    details: Optional[dict[str, Any]] = None
    status: str
    created_at: datetime
    user_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class LogListResponse(BaseModel):
    """List of activity logs."""
    items: List[LogResponse]
    total: int
