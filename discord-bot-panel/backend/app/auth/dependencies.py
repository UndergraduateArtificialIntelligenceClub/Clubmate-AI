from fastapi import Depends, HTTPException, Cookie
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models.user import User
from app.core.config import settings


async def get_current_user(
    access_token: str = Cookie(default=None),
    session: AsyncSession = Depends(get_session),
) -> User:
    # --- DEV MODE BYPASS ---
    # If no token is present, return a dummy admin user for development
    if not access_token:
        # return await get_dev_user(session) # You could fetch user 1
        return User(id=1, username="DevAdmin", discord_id="000000", is_admin=True)
    # -----------------------

    try:
        token = access_token.replace("Bearer ", "")
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401)
    except JWTError:
        raise HTTPException(401)

    user = await session.get(User, int(user_id))
    if not user:
        raise HTTPException(401)
    return user


async def get_current_admin(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "Admins only")
    return user
