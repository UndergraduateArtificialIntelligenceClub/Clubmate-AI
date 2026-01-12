"""
Stats Router
============
API endpoints for dashboard statistics.

Endpoints:
- GET /stats/ - Get system statistics
- GET /stats/logs - Get activity logs
- DELETE /stats/logs - Clear all logs
"""

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.stats import StatsResponse, LogResponse
from app.services.stats_service import StatsService


router = APIRouter()


@router.get("/", response_model=StatsResponse)
async def get_stats(
    session: AsyncSession = Depends(get_session),
):
    """
    Get dashboard statistics.
    
    Returns:
    - total_contacts: Number of contacts
    - total_files: Number of uploaded files
    - total_api_keys: Total API keys stored
    - active_api_keys: Number of active (non-revoked) API keys
    """
    stats = await StatsService.get_stats(session)
    return stats


@router.get("/logs", response_model=List[LogResponse])
async def get_logs(
    limit: int = Query(50, ge=1, le=500, description="Max logs to return"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get recent activity logs.
    
    Logs are returned in reverse chronological order (newest first).
    """
    logs, total = await StatsService.get_logs(session, limit=limit)
    return logs


@router.delete("/logs", status_code=204)
async def clear_logs(
    session: AsyncSession = Depends(get_session),
):
    """
    Clear all activity logs.
    
    Warning: This action is irreversible.
    """
    await StatsService.clear_logs(session)
    return None
