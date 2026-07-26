"""Tests for mcp_servers.google_forms — pure helpers and tool functions."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_servers.google_forms import (
    _extract_form_id,
)


class TestExtractFormId:
    def test_extracts_from_forms_url(self):
        url = "https://docs.google.com/forms/d/FORM123/edit"
        assert _extract_form_id(url) == "FORM123"

    def test_extracts_from_forms_google_com(self):
        url = "https://forms.google.com/d/FORM456/viewform"
        assert _extract_form_id(url) == "FORM456"

    def test_returns_bare_id(self):
        assert _extract_form_id("FORM123") == "FORM123"

    def test_empty_string(self):
        assert _extract_form_id("") == ""


class TestCreateForm:
    @patch("mcp_servers.google_forms.get_service")
    def test_creates_form_without_questions(self, mock_get_service):
        from mcp_servers.google_forms import create_form
        service = MagicMock()
        service.forms().create().execute.return_value = {"formId": "form123"}
        mock_get_service.return_value = service

        result = create_form("Test Form", "Description")
        assert result["form_id"] == "form123"
        assert result["title"] == "Test Form"
        # Merged main auto-adds a Name question for respondent identity
        service.forms().batchUpdate.assert_called_once()

    @patch("mcp_servers.google_forms.get_service")
    def test_creates_form_with_questions(self, mock_get_service):
        from mcp_servers.google_forms import create_form
        service = MagicMock()
        service.forms().create().execute.return_value = {"formId": "form456"}
        mock_get_service.return_value = service

        result = create_form("Survey", questions=[
            {"text": "Q1", "type": "short_answer"},
            {"text": "Q2", "type": "multiple_choice", "options": ["A", "B"]},
        ])
        assert result["form_id"] == "form456"
        assert result["title"] == "Survey"
        service.forms().batchUpdate.assert_called_once()


class TestGetFormResponses:
    @patch("mcp_servers.google_forms.get_service")
    def test_returns_responses(self, mock_get_service):
        from mcp_servers.google_forms import get_form_responses
        service = MagicMock()
        service.forms().get().execute.return_value = {
            "info": {"title": "Survey"},
            "items": [
                {"questionItem": {"question": {"questionId": "q1"}}, "title": "Name"}
            ],
        }
        service.forms().responses().list().execute.return_value = {
            "responses": [
                {
                    "responseId": "r1",
                    "createTime": "2026-03-15T10:00:00Z",
                    "answers": {
                        "q1": {"textAnswers": {"answers": [{"value": "Alice"}]}}
                    },
                }
            ]
        }
        mock_get_service.return_value = service

        result = get_form_responses("form123")
        assert result["total_responses"] == 1
        assert result["responses"][0]["Name"] == "Alice"


class TestGetFormInfo:
    @patch("mcp_servers.google_forms.get_service")
    def test_returns_form_info(self, mock_get_service):
        from mcp_servers.google_forms import get_form_info
        service = MagicMock()
        service.forms().get().execute.return_value = {
            "info": {"title": "Test Form", "description": "Desc"},
            "items": [{"title": "Q1"}, {"title": "Q2"}],
        }
        mock_get_service.return_value = service

        result = get_form_info("form123")
        assert result["title"] == "Test Form"
        assert result["question_count"] == 2
