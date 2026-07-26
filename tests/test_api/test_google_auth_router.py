"""Tests for api/routers/google_auth.py"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from api.routers.google_auth import _oauth_redirect_uri


class TestOauthRedirectUri:
    def test_with_request(self):
        request = MagicMock()
        request.base_url = "http://example.com:8000/"
        result = _oauth_redirect_uri(request)
        assert result == "http://example.com:8000/google/callback"

    def test_without_request_localhost(self):
        with patch("api.routers.google_auth.settings") as mock_settings:
            mock_settings.api_host = "0.0.0.0"
            mock_settings.api_port = 8000
            mock_settings.api_external_base_url = ""
            result = _oauth_redirect_uri(None)
        assert result == "http://localhost:8000/google/callback"

    def test_without_request_specific_host(self):
        with patch("api.routers.google_auth.settings") as mock_settings:
            mock_settings.api_host = "myhost.local"
            mock_settings.api_port = 9000
            mock_settings.api_external_base_url = ""
            result = _oauth_redirect_uri(None)
        assert result == "http://myhost.local:9000/google/callback"

    def test_without_request_ipv6(self):
        with patch("api.routers.google_auth.settings") as mock_settings:
            mock_settings.api_host = "::"
            mock_settings.api_port = 8000
            mock_settings.api_external_base_url = ""
            result = _oauth_redirect_uri(None)
        assert result == "http://localhost:8000/google/callback"

    def test_empty_host_defaults_to_localhost(self):
        with patch("api.routers.google_auth.settings") as mock_settings:
            mock_settings.api_host = ""
            mock_settings.api_port = 8000
            mock_settings.api_external_base_url = ""
            result = _oauth_redirect_uri(None)
        assert result == "http://localhost:8000/google/callback"


class TestGoogleStatus:
    def test_disconnected(self, client):
        resp = client.get("/google/status", headers={"Authorization": "Bearer test-token"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["connected"] is False
        assert data["account_email"] is None


class TestUploadCredentials:
    def test_upload_valid_json(self, client):
        creds = {"installed": {"client_id": "test", "client_secret": "test"}}
        resp = client.post(
            "/google/credentials",
            headers={"Authorization": "Bearer test-token"},
            json={"credentials_json": json.dumps(creds)},
        )
        assert resp.status_code == 200
        assert "saved" in resp.json()["message"].lower()

    def test_upload_invalid_json(self, client):
        resp = client.post(
            "/google/credentials",
            headers={"Authorization": "Bearer test-token"},
            json={"credentials_json": "not valid json"},
        )
        assert resp.status_code == 400


class TestDisconnectGoogle:
    def test_disconnect_when_no_token(self, client):
        resp = client.delete(
            "/google/disconnect",
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 200
        assert "disconnected" in resp.json()["message"].lower()
