from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.core.config import settings
from app.models.secure import GoogleToken
from app.auth.dependencies import get_current_admin
from app.models.user import User

router = APIRouter(prefix="/auth/google", tags=["Google"])


@router.get("/connect")
async def connect_google():
    scope = "https://www.googleapis.com/auth/userinfo.email"
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={settings.BASE_URL}/api/auth/google/callback&"
        "response_type=code&"
        f"scope={scope}&"
        "access_type=offline&"
        "prompt=consent"
    )
    return RedirectResponse(url)


@router.get("/callback")
async def google_callback(code: str, session: AsyncSession = Depends(get_session)):
    # Simulate success for User 1 (Admin)
    stmt = select(GoogleToken).where(GoogleToken.user_id == 1)
    existing = await session.exec(stmt)
    if not existing.first():
        gt = GoogleToken(
            user_id=1, encrypted_refresh_token=b"dummy", nonce=b"d", tag=b"d"
        )
        session.add(gt)
        await session.commit()

    # Redirect to frontend with status param for the Toast
    return RedirectResponse("http://localhost:5173/google?status=success")


@router.get("/status")
async def google_status(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_admin),
):
    stmt = select(GoogleToken).where(GoogleToken.user_id == user.id)
    res = await session.exec(stmt)
    return {"is_connected": res.first() is not None}


@router.delete("/disconnect")
async def disconnect_google(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_admin),
):
    stmt = select(GoogleToken).where(GoogleToken.user_id == user.id)
    results = await session.exec(stmt)
    token = results.first()

    if not token:
        raise HTTPException(status_code=404, detail="Not connected")

    await session.delete(token)
    await session.commit()
    return {"status": "disconnected"}
