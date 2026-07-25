"""Tests for bot.client — GeminiMCPClient."""

from unittest.mock import MagicMock, AsyncMock, patch
from types import SimpleNamespace

import pytest


class TestExtractFunctionCalls:
    """Test the static _extract_function_calls method."""

    def _import_client(self):
        from bot.client import GeminiMCPClient
        return GeminiMCPClient

    def test_no_function_calls_on_text_response(self):
        GeminiMCPClient = self._import_client()
        response = MagicMock()
        response.function_calls = []
        assert GeminiMCPClient._extract_function_calls(response) == []

    def test_extracts_from_function_calls_attribute(self):
        GeminiMCPClient = self._import_client()
        fc = MagicMock()
        response = MagicMock()
        response.function_calls = [fc]
        result = GeminiMCPClient._extract_function_calls(response)
        assert result == [fc]

    def test_extracts_from_candidates_parts(self):
        GeminiMCPClient = self._import_client()
        fc = MagicMock()
        part = SimpleNamespace(function_call=fc, text=None)
        content = SimpleNamespace(parts=[part])
        candidate = SimpleNamespace(content=content)
        response = MagicMock(spec=["candidates"])
        response.candidates = [candidate]
        result = GeminiMCPClient._extract_function_calls(response)
        assert result == [fc]

    def test_returns_empty_when_no_candidates(self):
        GeminiMCPClient = self._import_client()
        response = MagicMock(spec=["candidates"])
        response.candidates = []
        assert GeminiMCPClient._extract_function_calls(response) == []

    def test_skips_text_only_parts(self):
        GeminiMCPClient = self._import_client()
        part = SimpleNamespace(function_call=None, text="hello")
        content = SimpleNamespace(parts=[part])
        candidate = SimpleNamespace(content=content)
        response = MagicMock(spec=["candidates"])
        response.candidates = [candidate]
        assert GeminiMCPClient._extract_function_calls(response) == []


class TestExtractCandidateContent:
    def _import_client(self):
        from bot.client import GeminiMCPClient
        return GeminiMCPClient

    def test_returns_content_from_first_candidate(self):
        GeminiMCPClient = self._import_client()
        content = SimpleNamespace(parts=[])
        candidate = SimpleNamespace(content=content)
        response = MagicMock(spec=["candidates"])
        response.candidates = [candidate]
        assert GeminiMCPClient._extract_candidate_content(response) is content

    def test_returns_none_when_no_candidates(self):
        GeminiMCPClient = self._import_client()
        response = MagicMock(spec=["candidates"])
        response.candidates = []
        assert GeminiMCPClient._extract_candidate_content(response) is None

    def test_returns_none_when_no_candidates_attr(self):
        GeminiMCPClient = self._import_client()
        response = MagicMock(spec=[])
        assert GeminiMCPClient._extract_candidate_content(response) is None


class TestExtractText:
    def _import_client(self):
        from bot.client import GeminiMCPClient
        return GeminiMCPClient

    def test_returns_text_attribute(self):
        GeminiMCPClient = self._import_client()
        response = MagicMock()
        response.text = "Hello world"
        assert GeminiMCPClient._extract_text(response) == "Hello world"

    def test_returns_empty_string_when_no_text(self):
        GeminiMCPClient = self._import_client()
        response = MagicMock()
        response.text = ""
        assert GeminiMCPClient._extract_text(response) == ""

    def test_extracts_from_candidate_parts(self):
        GeminiMCPClient = self._import_client()
        part1 = SimpleNamespace(text="Line 1", function_call=None)
        part2 = SimpleNamespace(text="Line 2", function_call=None)
        content = SimpleNamespace(parts=[part1, part2])
        candidate = SimpleNamespace(content=content)
        response = MagicMock(spec=["candidates", "text"])
        response.text = None
        response.candidates = [candidate]
        result = GeminiMCPClient._extract_text(response)
        assert "Line 1" in result
        assert "Line 2" in result

    def test_returns_empty_for_no_parts(self):
        GeminiMCPClient = self._import_client()
        content = SimpleNamespace(parts=[])
        candidate = SimpleNamespace(content=content)
        response = MagicMock(spec=["candidates", "text"])
        response.text = None
        response.candidates = [candidate]
        assert GeminiMCPClient._extract_text(response) == ""


class TestClearHistory:
    def test_clears_history(self):
        from bot.client import GeminiMCPClient
        with patch("bot.client.genai"):
            client = GeminiMCPClient.__new__(GeminiMCPClient)
            client.history = [{"role": "user", "parts": [{"text": "hi"}]}]
            client.sessions = {}
            client.gemini = MagicMock()
            from contextlib import AsyncExitStack
            client.exit_stack = AsyncExitStack()
            client.clear_history()
            assert client.history == []


class TestRagAvailable:
    def test_returns_bool(self):
        from bot.client import GeminiMCPClient
        result = GeminiMCPClient.rag_available()
        assert isinstance(result, bool)
