"""Shared test fixtures for Clubmate AI tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

# Ensure project root is on sys.path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def mock_settings():
    """Patch config.settings with controlled test values."""
    settings = MagicMock()
    settings.discord_token = "test-discord-token"
    settings.discord_client_id = "test-client-id"
    settings.discord_client_secret = "test-client-secret"
    settings.discord_guild_id = "123456789"
    settings.exec_role_name = "Executive"
    settings.gemini_api_key = "test-gemini-key"
    settings.default_llm_model = "gemini-2.5-flash"
    settings.google_token_path = "/tmp/test_google_token.json"
    settings.google_credentials_path = "/tmp/test_google_credentials.json"
    settings.chroma_db_dir = "/tmp/test_chroma_db"
    settings.chroma_collection_name = "test-docs"
    settings.embedding_model = "BAAI/bge-base-en-v1.5"
    settings.top_k_results = 5
    settings.temperature = 0.7
    settings.chunk_threshold_type = "percentile"
    settings.chunk_threshold_amount = 95.0
    settings.api_host = "0.0.0.0"
    settings.api_port = 8000
    settings.api_secret_key = "test-secret"
    settings.meeting_summary_channel_id = "999999999"
    settings.whisper_mode = "local"
    settings.openai_api_key = "test-openai-key"
    return settings


@pytest.fixture
def mock_discord_role():
    """Create a mock discord.Role with a given name."""
    def _make_role(name: str):
        role = MagicMock()
        role.name = name
        return role
    return _make_role


@pytest.fixture
def mock_discord_member():
    """Create a mock discord.Member with configurable roles."""
    def _make_member(roles=None, is_member=True):
        member = MagicMock(spec=["id", "display_name", "roles", "voice"])
        member.id = 12345
        member.display_name = "TestUser"
        member.roles = roles or []
        return member
    return _make_member


@pytest.fixture
def mock_discord_interaction():
    """Create a mock discord.Interaction."""
    interaction = MagicMock()
    interaction.guild_id = 123456789
    interaction.user = MagicMock()
    interaction.user.roles = []
    interaction.user.voice = MagicMock()
    interaction.user.voice.channel = MagicMock()
    interaction.user.voice.channel.name = "Test Voice"
    interaction.user.voice.channel.connect = AsyncMock()
    return interaction


@pytest.fixture
def mock_google_service():
    """Create a chainable mock Google API service object."""
    service = MagicMock()
    return service


@pytest.fixture
def mock_genai_client():
    """Create a mock google.genai.Client."""
    client = MagicMock()
    client.aio = MagicMock()
    client.aio.models = MagicMock()
    client.aio.models.generate_content = AsyncMock()
    return client


@pytest.fixture
def client(mock_settings):
    """Create a FastAPI TestClient with mocked auth and settings."""
    from fastapi.testclient import TestClient
    from api.main import app

    def _mock_verify():
        return {"id": "12345", "username": "TestUser", "discriminator": "0"}

    with patch("api.routers.config.settings", mock_settings), \
         patch("api.routers.status.settings", mock_settings), \
         patch("api.routers.google_auth.settings", mock_settings):
        from api.auth import verify_discord_admin

        def _override():
            return {"id": "12345", "username": "TestUser", "discriminator": "0"}

        app.dependency_overrides[verify_discord_admin] = _override

        with TestClient(app, raise_server_exceptions=False) as c:
            yield c

        app.dependency_overrides.clear()
