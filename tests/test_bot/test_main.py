"""Tests for bot/main.py (SessionManager, ClubmateBot, main)"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from bot.main import SessionManager


class TestSessionManager:
    @pytest.fixture
    def sm(self):
        return SessionManager()

    @pytest.mark.asyncio
    async def test_get_creates_new_session(self, sm):
        with patch("bot.main.GeminiMCPClient") as MockClient:
            mock_instance = MagicMock()
            mock_instance.connect_all = AsyncMock()
            MockClient.return_value = mock_instance
            result = await sm.get(12345)
            assert result is mock_instance
            mock_instance.connect_all.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_reuses_existing_session(self, sm):
        with patch("bot.main.GeminiMCPClient") as MockClient:
            mock_instance = MagicMock()
            mock_instance.connect_all = AsyncMock()
            MockClient.return_value = mock_instance
            first = await sm.get(12345)
            second = await sm.get(12345)
            assert first is second
            assert MockClient.call_count == 1

    @pytest.mark.asyncio
    async def test_different_channels_get_different_sessions(self, sm):
        with patch("bot.main.GeminiMCPClient") as MockClient:
            mock_a = MagicMock()
            mock_a.connect_all = AsyncMock()
            mock_b = MagicMock()
            mock_b.connect_all = AsyncMock()
            MockClient.side_effect = [mock_a, mock_b]
            session_a = await sm.get(111)
            session_b = await sm.get(222)
            assert session_a is not session_b
            assert MockClient.call_count == 2

    @pytest.mark.asyncio
    async def test_close_all(self, sm):
        with patch("bot.main.GeminiMCPClient") as MockClient:
            mock_instance = MagicMock()
            mock_instance.connect_all = AsyncMock()
            mock_instance.close = AsyncMock()
            MockClient.return_value = mock_instance
            await sm.get(12345)
            await sm.close_all()
            mock_instance.close.assert_awaited_once()
            assert sm._sessions == {}

    @pytest.mark.asyncio
    async def test_close_all_empty(self, sm):
        await sm.close_all()
        assert sm._sessions == {}


class TestMainFunction:
    def test_main_exits_without_token(self):
        with patch("bot.main.settings") as mock_settings:
            mock_settings.discord_token = ""
            with pytest.raises(SystemExit):
                from bot.main import main
                main()

    def test_main_exits_without_token_none(self):
        with patch("bot.main.settings") as mock_settings:
            mock_settings.discord_token = None
            with pytest.raises(SystemExit):
                from bot.main import main
                main()
