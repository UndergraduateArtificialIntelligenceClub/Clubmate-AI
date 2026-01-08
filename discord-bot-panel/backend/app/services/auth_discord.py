import httpx
from fastapi import HTTPException
from app.core.config import settings

REDIRECT_URI = f"{settings.BASE_URL}/api/auth/discord/callback"

async def exchange_code(code: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://discord.com/api/oauth2/token",
            data={
                "client_id": settings.DISCORD_CLIENT_ID,
                "client_secret": settings.DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI
            }
        )
        if resp.status_code != 200:
            raise HTTPException(400, "Discord Auth Failed")
        return resp.json().get("access_token")

async def get_user_profile(token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {token}"}
        )
        return resp.json()
