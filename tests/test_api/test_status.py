"""Tests for api/routers/status.py"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


class TestGetStatus:
    def test_returns_bot_online(self, client):
        resp = client.get("/status", headers={"Authorization": "Bearer test-token"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["bot"] == "online"

    def test_rag_status_ready(self, client):
        resp = client.get("/status", headers={"Authorization": "Bearer test-token"})
        data = resp.json()
        assert data["rag"]["status"] in ("ready", "unavailable")

    def test_model_in_response(self, client):
        resp = client.get("/status", headers={"Authorization": "Bearer test-token"})
        data = resp.json()
        assert "model" in data
        assert isinstance(data["model"], str)

    def test_exec_role_in_response(self, client):
        resp = client.get("/status", headers={"Authorization": "Bearer test-token"})
        data = resp.json()
        assert "exec_role" in data

    def test_google_connected_is_boolean(self, client):
        resp = client.get("/status", headers={"Authorization": "Bearer test-token"})
        data = resp.json()
        assert isinstance(data["google_connected"], bool)
