import psutil
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models.contact import Contact
from app.models.audit import AuditLog
from app.auth.dependencies import get_current_admin

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("/")
async def get_system_stats(
    session: AsyncSession = Depends(get_session), user=Depends(get_current_admin)
):
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    contact_count = len((await session.exec(select(Contact))).all())
    banned_count = len(
        (await session.exec(select(Contact).where(Contact.status == "banned"))).all()
    )

    return {
        "cpu": cpu,
        "memory": mem,
        "total_contacts": contact_count,
        "active_bans": banned_count,
        "uptime": "99.9%",
    }


@router.get("/logs")
async def get_audit_logs(
    session: AsyncSession = Depends(get_session), user=Depends(get_current_admin)
):
    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(20)
    res = await session.exec(stmt)
    return res.all()


@router.delete("/logs")
async def clear_audit_logs(
    session: AsyncSession = Depends(get_session), user=Depends(get_current_admin)
):
    # In a real app, we might not want to delete ALL logs, but for this feature:
    stmt = select(AuditLog)
    results = await session.exec(stmt)
    for log in results:
        await session.delete(log)
    await session.commit()
    return {"status": "cleared"}
