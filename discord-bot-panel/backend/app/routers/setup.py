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

from app.config import get_settings

router = APIRouter()
settings = get_settings()

class SetupConfig(BaseModel):
    discord_client_id: str
    discord_client_secret: str
    google_client_id: str
    google_client_secret: str

@router.get("/status")
async def get_setup_status():
    """Check if the application is configured."""
    # Reload settings to ensure we have the latest env vars
    from app.config import get_settings
    current_settings = get_settings()
    
    # Check if Discord Client ID is set (minimal requirement)
    is_configured = bool(current_settings.discord_client_id and current_settings.discord_client_secret)
    
    return {
        "is_configured": is_configured,
        "discord_redirect_uri": current_settings.discord_redirect_uri,
        "google_redirect_uri": current_settings.google_redirect_uri
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
        set_key(env_path, "DISCORD_CLIENT_ID", config.discord_client_id)
        set_key(env_path, "DISCORD_CLIENT_SECRET", config.discord_client_secret)
        set_key(env_path, "GOOGLE_CLIENT_ID", config.google_client_id)
        set_key(env_path, "GOOGLE_CLIENT_SECRET", config.google_client_secret)
        
        # We also need to set the redirect URIs if they are missing
        # But we'll assume the defaults in config.py are correct for now
        # OR force them to be set here. Let's force them for safety.
        set_key(env_path, "DISCORD_REDIRECT_URI", "http://localhost:8000/api/auth/discord/callback")
        set_key(env_path, "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")
        
        # To make changes effective immediately without restart (if possible),
        # we update os.environ
        os.environ["DISCORD_CLIENT_ID"] = config.discord_client_id
        os.environ["DISCORD_CLIENT_SECRET"] = config.discord_client_secret
        os.environ["GOOGLE_CLIENT_ID"] = config.google_client_id
        os.environ["GOOGLE_CLIENT_SECRET"] = config.google_client_secret
        
        # Clear lru_cache for settings
        get_settings.cache_clear()
        
        return {"status": "success", "message": "Configuration saved. Please reload the page."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
