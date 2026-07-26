"""Tests for api.auth — Discord OAuth verification middleware."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


class TestVerifyDiscordAdmin:
    @pytest.mark.asyncio
    async def test_missing_authorization_header(self):
        from api.auth import verify_discord_admin
        with pytest.raises(HTTPException) as exc_info:
            await verify_discord_admin(authorization=None)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_authorization_format(self):
        from api.auth import verify_discord_admin
        with pytest.raises(HTTPException) as exc_info:
            await verify_discord_admin(authorization="InvalidToken")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_bearer_prefix(self):
        from api.auth import verify_discord_admin
        with pytest.raises(HTTPException) as exc_info:
            await verify_discord_admin(authorization="Token abc123")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    @patch("config.settings")
    async def test_invalid_discord_token(self, mock_settings, mock_httpx_cls):
        from api.auth import verify_discord_admin
        mock_settings.discord_guild_id = ""

        mock_response = MagicMock()
        mock_response.status_code = 401

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_cls.return_value = mock_client

        with pytest.raises(HTTPException) as exc_info:
            await verify_discord_admin(authorization="Bearer bad-token")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    @patch("config.settings")
    async def test_valid_token_no_guild_check(self, mock_settings, mock_httpx_cls):
        from api.auth import verify_discord_admin
        mock_settings.discord_guild_id = ""

        user_data = {"id": "123", "username": "testuser"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = user_data

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_cls.return_value = mock_client

        result = await verify_discord_admin(authorization="Bearer valid-token")
        assert result == user_data

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    @patch("config.settings")
    async def test_not_guild_member(self, mock_settings, mock_httpx_cls):
        from api.auth import verify_discord_admin
        mock_settings.discord_guild_id = "999"

        user_data = {"id": "123"}
        mock_user_response = MagicMock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = user_data

        mock_guilds_response = MagicMock()
        mock_guilds_response.status_code = 200
        mock_guilds_response.json.return_value = [{"id": "111", "permissions": "2147483647"}]

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=[mock_user_response, mock_guilds_response])
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_cls.return_value = mock_client

        with pytest.raises(HTTPException) as exc_info:
            await verify_discord_admin(authorization="Bearer valid-token")
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    @patch("config.settings")
    async def test_no_manage_guild_permission(self, mock_settings, mock_httpx_cls):
        from api.auth import verify_discord_admin
        mock_settings.discord_guild_id = "999"

        user_data = {"id": "123"}
        mock_user_response = MagicMock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = user_data

        mock_guilds_response = MagicMock()
        mock_guilds_response.status_code = 200
        mock_guilds_response.json.return_value = [{"id": "999", "permissions": "0"}]

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=[mock_user_response, mock_guilds_response])
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_cls.return_value = mock_client

        with pytest.raises(HTTPException) as exc_info:
            await verify_discord_admin(authorization="Bearer valid-token")
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    @patch("config.settings")
    async def test_has_manage_guild_permission(self, mock_settings, mock_httpx_cls):
        from api.auth import verify_discord_admin
        mock_settings.discord_guild_id = "999"

        user_data = {"id": "123", "username": "admin"}
        mock_user_response = MagicMock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = user_data

        mock_guilds_response = MagicMock()
        mock_guilds_response.status_code = 200
        mock_guilds_response.json.return_value = [{"id": "999", "permissions": "32"}]

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=[mock_user_response, mock_guilds_response])
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_cls.return_value = mock_client

        result = await verify_discord_admin(authorization="Bearer valid-token")
        assert result == user_data
