"""
Stats Service
=============
Dashboard statistics and activity log management.
"""

from typing import Optional, List

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contact, File, APIKey, ActivityLog


class StatsService:
    """
    Service for dashboard statistics and logs.
    """
    
    @staticmethod
    async def get_stats(session: AsyncSession) -> dict:
        """
        Get dashboard statistics.
        
        Returns counts of:
        - Total contacts
        - Total files
        - Total API keys
        - Active API keys
        """
        # Count contacts
        contact_count = (await session.execute(
            select(func.count()).select_from(Contact)
        )).scalar() or 0
        
        # Count files
        file_count = (await session.execute(
            select(func.count()).select_from(File)
        )).scalar() or 0
        
        # Count all API keys
        total_keys = (await session.execute(
            select(func.count()).select_from(APIKey)
        )).scalar() or 0
        
        # Count active API keys
        active_keys = (await session.execute(
            select(func.count()).select_from(APIKey).where(APIKey.is_active == True)
        )).scalar() or 0
        
        return {
            "total_contacts": contact_count,
            "total_files": file_count,
            "total_api_keys": total_keys,
            "active_api_keys": active_keys,
        }
    
    @staticmethod
    async def get_logs(
        session: AsyncSession,
        limit: int = 50,
    ) -> tuple[List[ActivityLog], int]:
        """
        Get recent activity logs.
        
        Returns most recent logs first.
        """
        count_query = select(func.count()).select_from(ActivityLog)
        total = (await session.execute(count_query)).scalar() or 0
        
        query = (
            select(ActivityLog)
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(query)
        logs = result.scalars().all()
        
        return list(logs), total
    
    @staticmethod
    async def clear_logs(
        session: AsyncSession,
        user_id: Optional[int] = None,
    ) -> int:
        """
        Clear all activity logs.
        
        Returns the number of logs deleted.
        """
        # Get count before deletion
        count = (await session.execute(
            select(func.count()).select_from(ActivityLog)
        )).scalar() or 0
        
        # Delete all logs
        await session.execute(delete(ActivityLog))
        await session.commit()
        
        # Log this action (meta!)
        log = ActivityLog(
            user_id=user_id,
            action="clear_logs",
            details={"logs_cleared": count},
            status="success",
        )
        session.add(log)
        await session.commit()
        
        return count
