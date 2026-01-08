from fastapi import APIRouter, Depends, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.db.session import get_session
from app.services import auth_discord
from app.models.user import User
from app.auth.jwt import create_access_token
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.get("/discord/login")
async def discord_login():
    scope = "identify email"
    url = f"https://discord.com/api/oauth2/authorize?client_id={settings.DISCORD_CLIENT_ID}&redirect_uri={settings.BASE_URL}/api/auth/discord/callback&response_type=code&scope={scope}"
    return RedirectResponse(url)

@router.get("/discord/callback")
async def discord_callback(code: str, response: Response, session: AsyncSession = Depends(get_session)):
    token = await auth_discord.exchange_code(code)
    profile = await auth_discord.get_user_profile(token)
    
    # Find or Create User
    stmt = select(User).where(User.discord_id == profile['id'])
    result = await session.exec(stmt)
    user = result.first()
    
    if not user:
        # First user is admin
        all_users = await session.exec(select(User))
        is_first = len(all_users.all()) == 0
        user = User(
            discord_id=profile['id'],
            username=profile['username'],
            email=profile.get('email'),
            is_admin=is_first
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    jwt_token = create_access_token({"sub": str(user.id)})
    
    # Redirect to frontend root
    resp = RedirectResponse("http://localhost:8000/") # Or PyWebView URL
    resp.set_cookie(key="access_token", value=f"Bearer {jwt_token}", httponly=True, samesite='lax')
    return resp
