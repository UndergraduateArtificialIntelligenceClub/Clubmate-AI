"""
Discord OAuth middleware for the FastAPI backend.
The Vercel frontend sends a Discord access token obtained via NextAuth.
This middleware verifies the token and checks the user is a guild admin.
"""

import logging
from typing import Optional

import httpx
from fastapi import Header, HTTPException, status

logger = logging.getLogger(__name__)

DISCORD_API = "https://discord.com/api/v10"


async def verify_discord_admin(
    authorization: Optional[str] = Header(None),
) -> dict:
    """
    FastAPI dependency — validates the Discord Bearer token in the Authorization header.
    Verifies the user is a member of the configured guild with Manage Server permission.
    Raises 401/403 on failure, returns the Discord user dict on success.
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from config import settings

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = authorization.removeprefix("Bearer ").strip()

    async with httpx.AsyncClient() as client:
        # Get user info
        user_res = await client.get(
            f"{DISCORD_API}/users/@me",
            headers={"Authorization": f"Bearer {token}"},
        )
        if user_res.status_code != 200:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Discord token")

        user = user_res.json()

        # Check guild membership + permissions
        if settings.discord_guild_id:
            member_res = await client.get(
                f"{DISCORD_API}/users/@me/guilds",
                headers={"Authorization": f"Bearer {token}"},
            )
            if member_res.status_code != 200:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not fetch guilds")

            guilds = member_res.json()
            guild = next(
                (g for g in guilds if str(g.get("id")) == str(settings.discord_guild_id)),
                None,
            )
            if not guild:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not a member of this server",
                )

            # Bit 0x20 = MANAGE_GUILD permission
            permissions = int(guild.get("permissions", 0))
            if not (permissions & 0x20) and not (permissions & 0x8):  # MANAGE_GUILD or ADMINISTRATOR
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You need Manage Server or Administrator permission",
                )

    return user
