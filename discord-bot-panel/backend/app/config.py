"""
Configuration Management
========================
Centralized configuration using Pydantic Settings.
Environment variables are loaded from .env file in project root.

Why Pydantic Settings?
- Type validation at startup (fail fast)
- Environment variable support with defaults
- Easy access throughout the application
"""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All sensitive values should be set via .env file or environment.
    """
    
    # ============================================================
    # DATABASE CONFIGURATION
    # ============================================================
    # Use absolute path for SQLite to avoid "split-brain" issues
    @property
    def database_url(self) -> str:
        """Construct absolute SQLite URL."""
        db_path = Path(__file__).parent.parent / "data" / "clubmate.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{db_path.absolute()}"
    
    # Connection pool settings for production scalability
    db_pool_size: int = 5
    db_max_overflow: int = 10
    
    # ============================================================
    # SECURITY
    # ============================================================
    # Secret key for JWT tokens (generate with: openssl rand -hex 32)
    secret_key: str = "dev-secret-key-change-in-production"
    
    # Algorithm for JWT encoding
    jwt_algorithm: str = "HS256"
    
    # Token expiration (in minutes)
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    
    # Fernet encryption key for API keys (generate with: from cryptography.fernet import Fernet; Fernet.generate_key())
    encryption_key: str = "your-fernet-key-here"
    
    # ============================================================
    # DISCORD CONFIGURATION
    # ============================================================
    discord_bot_token: Optional[str] = None
    discord_client_id: Optional[str] = None
    discord_client_secret: Optional[str] = None
    discord_redirect_uri: str = "http://localhost:8000/api/auth/discord/callback"
    
    # ============================================================
    # GOOGLE OAUTH (for Drive/Gmail integration)
    # ============================================================
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"
    
    # ============================================================
    # FILE STORAGE
    # ============================================================
    # Directory for uploaded files (relative to backend folder)
    upload_dir: str = "uploads"
    
    # Maximum file size in bytes (default: 50MB)
    max_file_size: int = 50 * 1024 * 1024
    
    # Allowed file extensions (comma-separated)
    allowed_extensions: str = "pdf,doc,docx,xls,xlsx,csv,txt,png,jpg,jpeg,gif"
    
    # ============================================================
    # APPLICATION
    # ============================================================
    # Environment: development, staging, production
    environment: str = "development"
    
    # CORS origins (allow everything for local webview)
    cors_origins: str = "*"
    
    # API prefix
    api_prefix: str = "/api"
    
    # Debug mode
    debug: bool = True
    
    model_config = SettingsConfigDict(
        # Load from .env file - try multiple locations
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra env vars not defined here
    )
    
    @property
    def upload_path(self) -> Path:
        """Get absolute path to upload directory."""
        return Path(__file__).parent.parent / self.upload_dir
    
    @property
    def cors_origin_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def allowed_extension_list(self) -> list[str]:
        """Parse allowed extensions from comma-separated string."""
        return [ext.strip().lower() for ext in self.allowed_extensions.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Using lru_cache ensures settings are only parsed once,
    improving performance on repeated access.
    """
    return Settings()
