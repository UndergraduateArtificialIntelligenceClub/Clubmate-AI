"""Tests for api/routers/config.py"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from api.routers.config import _read_env, _write_env_key


class TestReadEnv:
    def test_reads_valid_env(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("FOO=bar\nBAZ=qux\n")
        with patch("api.routers.config.ENV_PATH", env_file):
            result = _read_env()
        assert result == {"FOO": "bar", "BAZ": "qux"}

    def test_skips_comments(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("# comment\nFOO=bar\n")
        with patch("api.routers.config.ENV_PATH", env_file):
            result = _read_env()
        assert result == {"FOO": "bar"}

    def test_skips_blank_lines(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("\n\nFOO=bar\n\n")
        with patch("api.routers.config.ENV_PATH", env_file):
            result = _read_env()
        assert result == {"FOO": "bar"}

    def test_handles_missing_file(self, tmp_path):
        missing = tmp_path / "nonexistent.env"
        with patch("api.routers.config.ENV_PATH", missing):
            result = _read_env()
        assert result == {}

    def test_strips_whitespace(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("  FOO  =  bar  \n")
        with patch("api.routers.config.ENV_PATH", env_file):
            result = _read_env()
        assert result == {"FOO": "bar"}

    def test_handles_values_with_equals(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("TOKEN=abc=def=ghi\n")
        with patch("api.routers.config.ENV_PATH", env_file):
            result = _read_env()
        assert result == {"TOKEN": "abc=def=ghi"}


class TestWriteEnvKey:
    def test_appends_new_key(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("EXISTING=value\n")
        with patch("api.routers.config.ENV_PATH", env_file):
            _write_env_key("NEW_KEY", "new_value")
        assert "NEW_KEY=new_value" in env_file.read_text()
        assert "EXISTING=value" in env_file.read_text()

    def test_updates_existing_key(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("KEY=old_value\n")
        with patch("api.routers.config.ENV_PATH", env_file):
            _write_env_key("KEY", "new_value")
        assert "KEY=new_value" in env_file.read_text()
        assert "old_value" not in env_file.read_text()

    def test_creates_file_if_missing(self, tmp_path):
        env_file = tmp_path / ".env"
        with patch("api.routers.config.ENV_PATH", env_file):
            _write_env_key("NEW", "value")
        assert env_file.exists()
        assert "NEW=value" in env_file.read_text()

    def test_preserves_other_keys(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("A=1\nB=2\nC=3\n")
        with patch("api.routers.config.ENV_PATH", env_file):
            _write_env_key("B", "99")
        lines = env_file.read_text().strip().splitlines()
        assert "A=1" in lines
        assert "B=99" in lines
        assert "C=3" in lines


class TestGetConfig:
    def test_returns_config(self, client):
        resp = client.get("/config", headers={"Authorization": "Bearer test-token"})
        assert resp.status_code == 200
        data = resp.json()
        assert "exec_role_name" in data
        assert "default_llm_model" in data
        assert "temperature" in data
        assert "google_connected" in data

    def test_no_sensitive_keys(self, client):
        resp = client.get("/config", headers={"Authorization": "Bearer test-token"})
        data = resp.json()
        assert "discord_token" not in data
        assert "gemini_api_key" not in data


class TestUpdateConfig:
    def test_update_single_field(self, client):
        resp = client.patch(
            "/config",
            headers={"Authorization": "Bearer test-token"},
            json={"exec_role_name": "NewExec"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "exec_role_name" in data["updated"]

    def test_update_empty_body(self, client):
        resp = client.patch(
            "/config",
            headers={"Authorization": "Bearer test-token"},
            json={},
        )
        assert resp.status_code == 400

    def test_update_multiple_fields(self, client):
        resp = client.patch(
            "/config",
            headers={"Authorization": "Bearer test-token"},
            json={"exec_role_name": "Test", "temperature": 0.5},
        )
        assert resp.status_code == 200
        assert len(resp.json()["updated"]) == 2


class TestUpdateApiKeys:
    def test_update_gemini_key(self, client):
        resp = client.patch(
            "/config/keys",
            headers={"Authorization": "Bearer test-token"},
            json={"gemini_api_key": "new-key-123"},
        )
        assert resp.status_code == 200
        assert "gemini_api_key" in resp.json()["updated"]

    def test_update_empty_body(self, client):
        resp = client.patch(
            "/config/keys",
            headers={"Authorization": "Bearer test-token"},
            json={},
        )
        assert resp.status_code == 400

    def test_blank_string_filtered(self, client):
        resp = client.patch(
            "/config/keys",
            headers={"Authorization": "Bearer test-token"},
            json={"gemini_api_key": "", "discord_token": "   "},
        )
        assert resp.status_code == 400
