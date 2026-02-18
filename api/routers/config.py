"""
Config endpoints — read and write .env settings via the dashboard.
"""

import re
import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from api.auth import verify_discord_admin
from config import PROJECT_ROOT, settings

router = APIRouter(prefix="/config", tags=["config"])
ENV_PATH = PROJECT_ROOT / ".env"


class ConfigUpdate(BaseModel):
    exec_role_name: Optional[str] = None
    default_llm_model: Optional[str] = None
    meeting_summary_channel_id: Optional[str] = None
    whisper_mode: Optional[str] = None
    top_k_results: Optional[int] = None
    temperature: Optional[float] = None


class ApiKeysUpdate(BaseModel):
    """Sensitive API keys — stored in .env, never returned in GET responses."""
    discord_token: Optional[str] = None
    discord_client_id: Optional[str] = None
    discord_client_secret: Optional[str] = None
    discord_guild_id: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None


def _read_env() -> dict[str, str]:
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    return env


def _write_env_key(key: str, value: str):
    """Update or append a single key in the .env file."""
    content = ENV_PATH.read_text() if ENV_PATH.exists() else ""
    pattern = re.compile(rf"^{re.escape(key)}=.*$", re.MULTILINE)
    new_line = f"{key}={value}"
    if pattern.search(content):
        content = pattern.sub(new_line, content)
    else:
        content = content.rstrip() + f"\n{new_line}\n"
    ENV_PATH.write_text(content)


@router.get("")
async def get_config(_user: dict = Depends(verify_discord_admin)):
    """Return current non-sensitive configuration."""
    return {
        "exec_role_name": settings.exec_role_name,
        "default_llm_model": settings.default_llm_model,
        "meeting_summary_channel_id": settings.meeting_summary_channel_id,
        "whisper_mode": settings.whisper_mode,
        "top_k_results": settings.top_k_results,
        "temperature": settings.temperature,
        "embedding_model": settings.embedding_model,
        "google_connected": Path(settings.google_token_path).exists(),
        "discord_guild_id": settings.discord_guild_id,
    }


@router.patch("")
async def update_config(
    body: ConfigUpdate,
    _user: dict = Depends(verify_discord_admin),
):
    """Update one or more configuration values in .env."""
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    key_map = {
        "exec_role_name": "EXEC_ROLE_NAME",
        "default_llm_model": "DEFAULT_LLM_MODEL",
        "meeting_summary_channel_id": "MEETING_SUMMARY_CHANNEL_ID",
        "whisper_mode": "WHISPER_MODE",
        "top_k_results": "TOP_K_RESULTS",
        "temperature": "TEMPERATURE",
    }

    for field, value in updates.items():
        env_key = key_map.get(field)
        if env_key:
            _write_env_key(env_key, str(value))
            # Update in-memory settings so GET reflects the new value immediately
            setattr(settings, field, value)

    return {"message": "Configuration updated. Restart the bot for changes to take effect.", "updated": list(updates.keys())}


@router.patch("/keys")
async def update_api_keys(
    body: ApiKeysUpdate,
    _user: dict = Depends(verify_discord_admin),
):
    """
    Update sensitive API keys in .env (Discord token, Gemini key, etc.).
    Only fields with non-empty values are written. Existing values are preserved for blank fields.
    """
    updates = body.model_dump(exclude_none=True)
    # Filter out blank strings
    updates = {k: v for k, v in updates.items() if str(v).strip()}
    if not updates:
        raise HTTPException(status_code=400, detail="No keys to update")

    key_map = {
        "discord_token": "DISCORD_TOKEN",
        "discord_client_id": "DISCORD_CLIENT_ID",
        "discord_client_secret": "DISCORD_CLIENT_SECRET",
        "discord_guild_id": "DISCORD_GUILD_ID",
        "gemini_api_key": "GEMINI_API_KEY",
        "openai_api_key": "OPENAI_API_KEY",
    }

    for field, value in updates.items():
        env_key = key_map.get(field)
        if env_key:
            _write_env_key(env_key, str(value))
            # Update in-memory settings so the bot picks up keys without restart where possible
            setattr(settings, field, value)

    return {
        "message": "API keys updated. Restart the bot for changes to take effect.",
        "updated": list(updates.keys()),
    }
