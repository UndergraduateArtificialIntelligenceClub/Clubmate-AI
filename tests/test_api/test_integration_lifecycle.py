"""Integration tests for the FastAPI API full request lifecycle.

Tests the complete HTTP request path: CORS → router → real auth middleware
(mocked Discord API via httpx) → handler → response.

No dependency_overrides — the real verify_discord_admin function is exercised.
"""

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config import settings


# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_discord_user_response():
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    resp.json.return_value = {
        "id": "111222333",
        "username": "TestAdmin",
        "discriminator": "0",
        "global_name": "Test Admin",
    }
    return resp


def _make_discord_guilds_response(has_manage_guild=True):
    perm = 0x20 if has_manage_guild else 0x0
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    resp.json.return_value = [
        {"id": "123456789", "name": "Test Guild", "permissions": str(perm)}
    ]
    return resp


def _make_discord_guilds_response_empty():
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    resp.json.return_value = [
        {"id": "999999999", "name": "Other Guild", "permissions": "0"}
    ]
    return resp


def _make_discord_token_invalid():
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 401
    return resp


class _FakeAsyncClient:
    def __init__(self, user_resp=None, guilds_resp=None):
        self._user_resp = user_resp or _make_discord_user_response()
        self._guilds_resp = guilds_resp or _make_discord_guilds_response()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def get(self, url, headers=None):
        if "/users/@me/guilds" in url:
            return self._guilds_resp
        return self._user_resp


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def authed_client():
    """FastAPI TestClient with real auth middleware (Discord API mocked via httpx)."""
    from fastapi.testclient import TestClient
    from api.main import app

    fake_client = _FakeAsyncClient()
    original_guild_id = settings.discord_guild_id
    settings.discord_guild_id = "123456789"

    with patch("api.auth.httpx.AsyncClient", return_value=fake_client):
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c

    settings.discord_guild_id = original_guild_id


@pytest.fixture
def unauthed_client():
    """FastAPI TestClient — no auth mocking (used for testing rejection)."""
    from fastapi.testclient import TestClient
    from api.main import app

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ── Public endpoints (no auth required) ───────────────────────────────────────


class TestPublicEndpoints:
    def test_health(self, unauthed_client):
        resp = unauthed_client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_root(self, unauthed_client):
        resp = unauthed_client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "Clubmate AI API"
        assert data["version"] == "1.0.0"


# ── Auth rejection (no token / bad token) ─────────────────────────────────────


class TestAuthRejection:
    def test_missing_auth_header(self, unauthed_client):
        resp = unauthed_client.get("/status")
        assert resp.status_code == 401
        assert "Authorization" in resp.json()["detail"]

    def test_invalid_bearer_format(self, unauthed_client):
        resp = unauthed_client.get("/status", headers={"Authorization": "Token abc"})
        assert resp.status_code == 401

    def test_invalid_discord_token(self):
        from fastapi.testclient import TestClient
        from api.main import app

        bad_client = _FakeAsyncClient(
            user_resp=_make_discord_token_invalid(),
            guilds_resp=_make_discord_token_invalid(),
        )
        original_guild_id = settings.discord_guild_id
        settings.discord_guild_id = "123456789"

        with patch("api.auth.httpx.AsyncClient", return_value=bad_client):
            with TestClient(app, raise_server_exceptions=False) as c:
                resp = c.get("/status", headers={"Authorization": "Bearer bad-token"})

        settings.discord_guild_id = original_guild_id
        assert resp.status_code == 401


# ── Guild / permission checks ─────────────────────────────────────────────────


class TestGuildChecks:
    def test_not_guild_member(self):
        from fastapi.testclient import TestClient
        from api.main import app

        fake = _FakeAsyncClient(
            user_resp=_make_discord_user_response(),
            guilds_resp=_make_discord_guilds_response_empty(),
        )
        original_guild_id = settings.discord_guild_id
        settings.discord_guild_id = "123456789"

        with patch("api.auth.httpx.AsyncClient", return_value=fake):
            with TestClient(app, raise_server_exceptions=False) as c:
                resp = c.get("/status", headers={"Authorization": "Bearer valid-token"})

        settings.discord_guild_id = original_guild_id
        assert resp.status_code == 403
        assert "not a member" in resp.json()["detail"].lower()

    def test_no_manage_guild_permission(self):
        from fastapi.testclient import TestClient
        from api.main import app

        fake = _FakeAsyncClient(
            user_resp=_make_discord_user_response(),
            guilds_resp=_make_discord_guilds_response(has_manage_guild=False),
        )
        original_guild_id = settings.discord_guild_id
        settings.discord_guild_id = "123456789"

        with patch("api.auth.httpx.AsyncClient", return_value=fake):
            with TestClient(app, raise_server_exceptions=False) as c:
                resp = c.get("/status", headers={"Authorization": "Bearer valid-token"})

        settings.discord_guild_id = original_guild_id
        assert resp.status_code == 403
        assert "manage" in resp.json()["detail"].lower()


# ── Authenticated endpoint tests ──────────────────────────────────────────────


class TestStatusEndpoint:
    def test_returns_bot_status(self, authed_client):
        resp = authed_client.get("/status", headers={"Authorization": "Bearer valid-token"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["bot"] == "online"
        assert "rag" in data
        assert "model" in data
        assert "exec_role" in data
        assert isinstance(data["google_connected"], bool)


class TestConfigEndpoint:
    def test_get_config_no_sensitive_keys(self, authed_client):
        resp = authed_client.get("/config", headers={"Authorization": "Bearer valid-token"})
        assert resp.status_code == 200
        data = resp.json()
        assert "exec_role_name" in data
        assert "discord_token" not in data
        assert "gemini_api_key" not in data

    def test_patch_config_persists_to_env(self, authed_client, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("EXEC_ROLE_NAME=OldExec\n")

        with patch("api.routers.config.ENV_PATH", env_file):
            resp = authed_client.patch(
                "/config",
                headers={"Authorization": "Bearer valid-token"},
                json={"exec_role_name": "NewExec"},
            )
        assert resp.status_code == 200
        assert "exec_role_name" in resp.json()["updated"]

        content = env_file.read_text()
        assert "EXEC_ROLE_NAME=NewExec" in content
        assert "OldExec" not in content

    def test_patch_config_empty_body_returns_400(self, authed_client):
        resp = authed_client.patch(
            "/config",
            headers={"Authorization": "Bearer valid-token"},
            json={},
        )
        assert resp.status_code == 400

    def test_patch_api_keys_persists_to_env(self, authed_client, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("GEMINI_API_KEY=old-key\n")

        with patch("api.routers.config.ENV_PATH", env_file):
            resp = authed_client.patch(
                "/config/keys",
                headers={"Authorization": "Bearer valid-token"},
                json={"gemini_api_key": "new-key-abc"},
            )
        assert resp.status_code == 200
        content = env_file.read_text()
        assert "GEMINI_API_KEY=new-key-abc" in content


class TestGoogleAuthEndpoints:
    def test_google_status_disconnected(self, authed_client):
        resp = authed_client.get("/google/status", headers={"Authorization": "Bearer valid-token"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["connected"] is False
        assert data["account_email"] is None

    def test_upload_credentials_valid(self, authed_client):
        creds = {"installed": {"client_id": "test", "client_secret": "test"}}
        resp = authed_client.post(
            "/google/credentials",
            headers={"Authorization": "Bearer valid-token"},
            json={"credentials_json": json.dumps(creds)},
        )
        assert resp.status_code == 200
        assert "saved" in resp.json()["message"].lower()

    def test_upload_credentials_invalid_json(self, authed_client):
        resp = authed_client.post(
            "/google/credentials",
            headers={"Authorization": "Bearer valid-token"},
            json={"credentials_json": "not-json"},
        )
        assert resp.status_code == 400

    def test_disconnect(self, authed_client):
        resp = authed_client.delete(
            "/google/disconnect",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert resp.status_code == 200
        assert "disconnected" in resp.json()["message"].lower()


class TestRAGEndpoints:
    def test_rag_status(self, authed_client):
        resp = authed_client.get("/rag/status", headers={"Authorization": "Bearer valid-token"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert "has_documents" in data
        assert "chunk_count" in data

    def test_rag_reset(self, authed_client):
        with patch("ragbot.rag.db_reset", return_value=True):
            resp = authed_client.delete(
                "/rag/reset",
                headers={"Authorization": "Bearer valid-token"},
            )
        assert resp.status_code == 200
        assert "cleared" in resp.json()["message"].lower()

    def test_rag_ingest_unsupported_file(self, authed_client):
        resp = authed_client.post(
            "/rag/ingest/file",
            headers={"Authorization": "Bearer valid-token"},
            files={"file": ("malware.exe", b"binary", "application/octet-stream")},
        )
        assert resp.status_code == 400

    def test_rag_ingest_file_success(self, authed_client):
        with patch("ragbot.rag.rag_ingest", return_value=True):
            resp = authed_client.post(
                "/rag/ingest/file",
                headers={"Authorization": "Bearer valid-token"},
                files={"file": ("notes.txt", b"Some meeting notes content.", "text/plain")},
            )
        assert resp.status_code == 200
        assert "ingested" in resp.json()["message"].lower()
