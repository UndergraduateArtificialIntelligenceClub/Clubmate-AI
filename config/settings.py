"""
Shared settings for Clubmate AI.
Single source of truth for all configuration — used by bot, API, and RAG.
Reads from .env at project root via Pydantic Settings.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Discord ──────────────────────────────────────────────────────────────
    # Required to start the bot — set in .env or via dashboard before first run
    discord_token: str = ""
    discord_client_id: str = ""
    discord_client_secret: str = ""
    discord_guild_id: str = ""

    # Exec role name — members with this role can use admin commands
    exec_role_name: str = "Executive"

    # ── Gemini ───────────────────────────────────────────────────────────────
    # Required for AI features — set in .env or via dashboard
    gemini_api_key: str = ""
    default_llm_model: str = "gemini-2.5-flash"

    # ── Google OAuth (populated after dashboard setup) ───────────────────────
    google_client_id: str = ""
    google_client_secret: str = ""
    # Path to stored Google token JSON (written by API after OAuth flow)
    google_token_path: str = str(PROJECT_ROOT / "data" / "google_token.json")
    # Path to Google credentials JSON (OAuth client secrets)
    google_credentials_path: str = str(PROJECT_ROOT / "data" / "google_credentials.json")

    # ── RAG ──────────────────────────────────────────────────────────────────
    chroma_db_dir: str = str(PROJECT_ROOT / "data" / "chroma_db")
    chroma_collection_name: str = "clubmate-docs"
    embedding_model: str = "BAAI/bge-base-en-v1.5"
    top_k_results: int = 5
    temperature: float = 0.7
    chunk_threshold_type: str = "percentile"
    chunk_threshold_amount: float = 95.0

    # ── API ───────────────────────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    # Secret key for signing JWT sessions in the API
    api_secret_key: str = "change-me-in-production"
    # Public API base URL used for OAuth callbacks behind proxies/load balancers.
    # Example: https://api.clubmate.yourclub.ca
    api_external_base_url: str = ""
    # Comma-separated allowed frontend origins for CORS.
    # Example: https://clubmate.yourclub.ca,https://staging.clubmate.yourclub.ca
    frontend_origins: str = "http://frontend:3000,http://localhost:3000,http://127.0.0.1:3000"

    # ── Meeting Transcription ─────────────────────────────────────────────────
    # Channel ID where meeting summaries are posted after a session ends
    meeting_summary_channel_id: str = ""
    # "gemini" uses Gemini audio transcription (uses GEMINI_API_KEY)
    # "local" uses local Whisper model, "api" uses OpenAI Whisper API
    whisper_mode: str = "gemini"
    openai_api_key: str = ""  # only needed if whisper_mode = "api"


# Singleton — import this everywhere instead of constructing Settings() each time
settings = Settings()
