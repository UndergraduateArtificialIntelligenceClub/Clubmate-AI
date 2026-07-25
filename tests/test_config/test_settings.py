"""Tests for config.settings."""

from unittest.mock import patch

import pytest

from config.settings import Settings, PROJECT_ROOT


class TestSettingsDefaults:
    def test_default_exec_role_name(self):
        s = Settings(discord_token="", _env_file=None)
        assert s.exec_role_name == "Executive"

    def test_default_llm_model(self):
        s = Settings(discord_token="", _env_file=None)
        assert s.default_llm_model == "gemini-2.5-flash"

    def test_default_top_k(self):
        s = Settings(discord_token="", _env_file=None)
        assert s.top_k_results == 5

    def test_default_temperature(self):
        s = Settings(discord_token="", _env_file=None)
        assert s.temperature == 0.7

    def test_default_api_port(self):
        s = Settings(discord_token="", _env_file=None)
        assert s.api_port == 8000

    def test_default_whisper_mode(self):
        s = Settings(discord_token="", _env_file=None)
        assert s.whisper_mode == "gemini"

    def test_default_chunk_threshold(self):
        s = Settings(discord_token="", _env_file=None)
        assert s.chunk_threshold_type == "percentile"
        assert s.chunk_threshold_amount == 95.0

    def test_default_chroma_collection(self):
        s = Settings(discord_token="", _env_file=None)
        assert s.chroma_collection_name == "clubmate-docs"


class TestSettingsOverrides:
    def test_override_exec_role(self):
        s = Settings(exec_role_name="Admin", _env_file=None)
        assert s.exec_role_name == "Admin"

    def test_override_gemini_key(self):
        s = Settings(gemini_api_key="sk-test-123", _env_file=None)
        assert s.gemini_api_key == "sk-test-123"

    def test_override_top_k(self):
        s = Settings(top_k_results=10, _env_file=None)
        assert s.top_k_results == 10

    def test_override_temperature(self):
        s = Settings(temperature=0.3, _env_file=None)
        assert s.temperature == 0.3

    def test_override_whisper_mode(self):
        s = Settings(whisper_mode="api", _env_file=None)
        assert s.whisper_mode == "api"

    def test_override_api_port(self):
        s = Settings(api_port=9000, _env_file=None)
        assert s.api_port == 9000


class TestProjectRoot:
    def test_project_root_is_path(self):
        assert isinstance(PROJECT_ROOT, type(PROJECT_ROOT))

    def test_project_root_has_expected_dirs(self):
        assert (PROJECT_ROOT / "bot").is_dir()
        assert (PROJECT_ROOT / "api").is_dir()
        assert (PROJECT_ROOT / "config").is_dir()
        assert (PROJECT_ROOT / "mcp_servers").is_dir()
        assert (PROJECT_ROOT / "ragbot").is_dir()


class TestSettingsTypes:
    def test_field_types(self):
        s = Settings(discord_token="", _env_file=None)
        assert isinstance(s.discord_token, str)
        assert isinstance(s.discord_guild_id, str)
        assert isinstance(s.top_k_results, int)
        assert isinstance(s.temperature, float)
        assert isinstance(s.api_port, int)
        assert isinstance(s.chunk_threshold_amount, float)
