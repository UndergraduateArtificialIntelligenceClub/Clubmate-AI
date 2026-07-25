"""Tests for mcp_servers.google_auth — credential loading and service building."""

from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest


class TestGetCredentials:
    @patch("mcp_servers.google_auth.Credentials.from_authorized_user_file")
    @patch("mcp_servers.google_auth.settings")
    def test_valid_credentials(self, mock_settings, mock_from_file):
        from mcp_servers.google_auth import get_credentials

        mock_settings.google_token_path = "/tmp/token.json"

        with patch("mcp_servers.google_auth.Path") as mock_path_cls:
            mock_token_path = MagicMock()
            mock_token_path.exists.return_value = True
            mock_path_cls.return_value = mock_token_path

            creds = MagicMock()
            creds.valid = True
            mock_from_file.return_value = creds

            result = get_credentials()
            assert result is creds

    @patch("mcp_servers.google_auth.Credentials.from_authorized_user_file")
    @patch("mcp_servers.google_auth.settings")
    def test_expired_credentials_refresh(self, mock_settings, mock_from_file):
        from mcp_servers.google_auth import get_credentials

        mock_settings.google_token_path = "/tmp/token.json"

        with patch("mcp_servers.google_auth.Path") as mock_path_cls:
            mock_token_path = MagicMock()
            mock_token_path.exists.return_value = True
            mock_token_path.parent = MagicMock()
            mock_path_cls.return_value = mock_token_path

            creds = MagicMock()
            creds.valid = False
            creds.expired = True
            creds.refresh_token = "refresh-tok"
            creds.to_json.return_value = '{"token": "new"}'
            mock_from_file.return_value = creds

            with patch("mcp_servers.google_auth.Request"):
                result = get_credentials()
                assert result is creds
                creds.refresh.assert_called_once()

    @patch("mcp_servers.google_auth.settings")
    def test_no_token_file_raises(self, mock_settings):
        from mcp_servers.google_auth import get_credentials

        mock_settings.google_token_path = "/tmp/token.json"

        with patch("mcp_servers.google_auth.Path") as mock_path_cls:
            mock_token_path = MagicMock()
            mock_token_path.exists.return_value = False
            mock_path_cls.return_value = mock_token_path

            with pytest.raises(ValueError, match="not connected"):
                get_credentials()

    @patch("mcp_servers.google_auth.Credentials.from_authorized_user_file")
    @patch("mcp_servers.google_auth.settings")
    def test_expired_refresh_fails_raises(self, mock_settings, mock_from_file):
        from mcp_servers.google_auth import get_credentials

        mock_settings.google_token_path = "/tmp/token.json"

        with patch("mcp_servers.google_auth.Path") as mock_path_cls:
            mock_token_path = MagicMock()
            mock_token_path.exists.return_value = True
            mock_path_cls.return_value = mock_token_path

            creds = MagicMock()
            creds.valid = False
            creds.expired = True
            creds.refresh_token = "refresh-tok"
            creds.refresh.side_effect = Exception("Refresh failed")
            mock_from_file.return_value = creds

            with pytest.raises(ValueError, match="could not be refreshed"):
                get_credentials()


class TestGetService:
    @patch("mcp_servers.google_auth.build")
    @patch("mcp_servers.google_auth.get_credentials")
    def test_builds_service(self, mock_get_creds, mock_build):
        from mcp_servers.google_auth import get_service

        creds = MagicMock()
        mock_get_creds.return_value = creds

        result = get_service("calendar", "v3")
        mock_build.assert_called_once_with("calendar", "v3", credentials=creds)
        assert result is mock_build.return_value
