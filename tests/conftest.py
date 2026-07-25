"""Shared test fixtures for Clubmate AI tests."""

import shutil
import sys
import tempfile
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


# ── Integration test fixtures ──────────────────────────────────────────────────


class FakeEmbeddings:
    """Deterministic fake embeddings for integration tests. Returns fixed-dimension
    random-but-seeded vectors so ChromaDB indexing/search works without downloading
    a real HuggingFace model."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def embed_documents(self, texts):
        return [self._embed(text) for text in texts]

    def embed_query(self, text):
        return self._embed(text)

    def _embed(self, text: str):
        import hashlib
        h = hashlib.sha256(text.encode()).digest()
        # Expand/truncate to desired dimension
        raw = list(h)
        while len(raw) < self.dimension:
            raw.extend(raw)
        vec = [float(b) / 255.0 for b in raw[:self.dimension]]
        # Normalize
        norm = sum(v * v for v in vec) ** 0.5
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec


@pytest.fixture
def tmp_chroma_dir():
    """Yield a temporary directory for ChromaDB, cleaned up after test."""
    d = tempfile.mkdtemp(prefix="clubmate_test_chroma_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def rag_with_temp_db(tmp_chroma_dir):
    """Create a real RAGSystem backed by a temp ChromaDB dir with fake embeddings.
    Resets the singleton between tests."""
    from ragbot.rag import RAGSystem, RAGConfig, _rag
    import ragbot.rag as rag_mod
    from config import settings

    # Reset singleton
    RAGSystem._instance = None
    RAGSystem._initialized = False
    rag_mod._rag = None

    # Point config to temp dir
    original_db_dir = RAGConfig.CHROMA_DB_DIR
    original_collection = RAGConfig.CHROMA_COLLECTION_NAME
    original_gemini_key = RAGConfig.GEMINI_API_KEY
    original_settings_db = settings.chroma_db_dir
    original_settings_col = settings.chroma_collection_name
    RAGConfig.CHROMA_DB_DIR = tmp_chroma_dir
    RAGConfig.CHROMA_COLLECTION_NAME = "test-integration"
    RAGConfig.GEMINI_API_KEY = "test-fake-key"
    settings.chroma_db_dir = tmp_chroma_dir
    settings.chroma_collection_name = "test-integration"
    settings.gemini_api_key = "test-fake-key"

    # Patch embeddings creation to use our fake
    with patch("ragbot.rag.create_embeddings", return_value=FakeEmbeddings()):
        # Force re-init
        RAGSystem._instance = None
        RAGSystem._initialized = False
        rag_mod._rag = None

        yield RAGConfig

    # Teardown
    RAGSystem._instance = None
    RAGSystem._initialized = False
    rag_mod._rag = None
    RAGConfig.CHROMA_DB_DIR = original_db_dir
    RAGConfig.CHROMA_COLLECTION_NAME = original_collection
    RAGConfig.GEMINI_API_KEY = original_gemini_key
    settings.chroma_db_dir = original_settings_db
    settings.chroma_collection_name = original_settings_col


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
