"""Tests for api/routers/rag.py"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


class TestRagStatus:
    def test_returns_ready(self, client):
        resp = client.get("/rag/status", headers={"Authorization": "Bearer test-token"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert "has_documents" in data
        assert "chunk_count" in data


class TestIngestFile:
    def test_ingest_success(self, client):
        with patch("ragbot.rag.rag_ingest", return_value=True):
            resp = client.post(
                "/rag/ingest/file",
                headers={"Authorization": "Bearer test-token"},
                files={"file": ("test.txt", b"Hello world content", "text/plain")},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "ingested" in data["message"].lower()

    def test_unsupported_file_type(self, client):
        resp = client.post(
            "/rag/ingest/file",
            headers={"Authorization": "Bearer test-token"},
            files={"file": ("test.exe", b"binary", "application/octet-stream")},
        )
        assert resp.status_code == 400


class TestIngestGoogleDoc:
    def test_ingest_google_doc_success(self, client):
        with patch("ragbot.rag.rag_ingest", return_value=True):
            with patch("ragbot.sources.google_docs.fetch_google_doc_text", return_value=("Title", "Content")):
                resp = client.post(
                    "/rag/ingest/google-doc",
                    headers={"Authorization": "Bearer test-token"},
                    json={"url": "https://docs.google.com/document/d/abc123/edit"},
                )
        assert resp.status_code == 200


class TestResetRag:
    def test_reset_success(self, client):
        with patch("ragbot.rag.db_reset", return_value=True):
            resp = client.delete("/rag/reset", headers={"Authorization": "Bearer test-token"})
        assert resp.status_code == 200
        data = resp.json()
        assert "cleared" in data["message"].lower()
