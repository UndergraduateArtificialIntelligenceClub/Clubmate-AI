"""
Setup Router
===========
Endpoints for initial application configuration.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from dotenv import set_key
from multiprocessing import Process
import sys
import time
from typing import Optional

from app.config import get_settings

router = APIRouter()
settings = get_settings()

class SetupConfig(BaseModel):
    discord_bot_token: str
    discord_client_id: Optional[str] = None
    discord_client_secret: Optional[str] = None
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None

@router.get("/status")
async def get_setup_status():
    """Check if the application is configured."""
    # Reload settings to ensure we have the latest env vars
    from app.config import get_settings
    current_settings = get_settings()
    
    # Check if a Bot Token is set (now the primary requirement)
    is_configured = bool(current_settings.discord_bot_token)
    
    return {
        "is_configured": is_configured,
        "discord_redirect_uri": current_settings.discord_redirect_uri,
        "google_redirect_uri": current_settings.google_redirect_uri,
        "has_discord_oauth": bool(current_settings.discord_client_id and current_settings.discord_client_secret)
    }

@router.post("/config")
async def save_config(config: SetupConfig):
    """Save configuration to .env file."""
    env_path = os.path.join(os.getcwd(), ".env")
    if not os.path.exists(env_path):
        # Create empty .env if it doesn't exist
        with open(env_path, "w") as f:
            f.write("")
    
    try:
        # Update .env file
        set_key(env_path, "DISCORD_BOT_TOKEN", config.discord_bot_token)
        if config.discord_client_id:
            set_key(env_path, "DISCORD_CLIENT_ID", config.discord_client_id)
        if config.discord_client_secret:
            set_key(env_path, "DISCORD_CLIENT_SECRET", config.discord_client_secret)
        if config.google_client_id:
            set_key(env_path, "GOOGLE_CLIENT_ID", config.google_client_id)
        if config.google_client_secret:
            set_key(env_path, "GOOGLE_CLIENT_SECRET", config.google_client_secret)
        
        # We also need to set the redirect URIs if they are missing
        set_key(env_path, "DISCORD_REDIRECT_URI", "http://localhost:8000/api/auth/discord/callback")
        set_key(env_path, "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")
        
        # To make changes effective immediately without restart (if possible),
        # we update os.environ
        os.environ["DISCORD_BOT_TOKEN"] = config.discord_bot_token
        if config.discord_client_id: os.environ["DISCORD_CLIENT_ID"] = config.discord_client_id
        if config.discord_client_secret: os.environ["DISCORD_CLIENT_SECRET"] = config.discord_client_secret
        if config.google_client_id: os.environ["GOOGLE_CLIENT_ID"] = config.google_client_id
        if config.google_client_secret: os.environ["GOOGLE_CLIENT_SECRET"] = config.google_client_secret
        
        # Clear lru_cache for settings
        get_settings.cache_clear()
        
        return {"status": "success", "message": "Configuration saved. Please reload the page."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
