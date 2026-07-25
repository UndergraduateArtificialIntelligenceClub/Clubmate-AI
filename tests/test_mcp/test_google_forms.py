"""Tests for mcp_servers.google_forms — pure helpers and tool functions."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_servers.google_forms import (
    _extract_form_id,
    _looks_like_name_question,
    _ensure_name_question,
    _question_to_item,
    _build_create_item_requests,
    _extract_answer_text,
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


class TestLooksLikeNameQuestion:
    def test_name_variants(self):
        assert _looks_like_name_question("Name") is True
        assert _looks_like_name_question("Full Name") is True
        assert _looks_like_name_question("your name?") is True
        assert _looks_like_name_question("NAME") is True

    def test_non_name_questions(self):
        assert _looks_like_name_question("Email") is False
        assert _looks_like_name_question("What is your major?") is False
        assert _looks_like_name_question("") is False


class TestEnsureNameQuestion:
    def test_prepends_name_when_missing(self):
        questions = [{"text": "Email", "type": "short_answer"}]
        result = _ensure_name_question(questions)
        assert len(result) == 2
        assert result[0]["text"] == "Name"
        assert result[0]["required"] is True

    def test_no_prepends_when_name_exists(self):
        questions = [{"text": "Your Name", "type": "short_answer"}]
        result = _ensure_name_question(questions)
        assert len(result) == 1
        assert result[0]["text"] == "Your Name"

    def test_handles_none(self):
        result = _ensure_name_question(None)
        assert len(result) == 1
        assert result[0]["text"] == "Name"

    def test_handles_empty_list(self):
        result = _ensure_name_question([])
        assert len(result) == 1
        assert result[0]["text"] == "Name"


class TestQuestionToItem:
    def test_short_answer(self):
        item = _question_to_item({"text": "Q1", "type": "short_answer"})
        assert item["title"] == "Q1"
        assert "textQuestion" in item["questionItem"]["question"]
        assert item["questionItem"]["question"]["textQuestion"]["paragraph"] is False

    def test_paragraph(self):
        item = _question_to_item({"text": "Q2", "type": "paragraph"})
        assert item["questionItem"]["question"]["textQuestion"]["paragraph"] is True

    def test_multiple_choice(self):
        item = _question_to_item({"text": "Q3", "type": "multiple_choice", "options": ["A", "B"]})
        assert item["questionItem"]["question"]["choiceQuestion"]["type"] == "RADIO"
        assert len(item["questionItem"]["question"]["choiceQuestion"]["options"]) == 2

    def test_checkbox(self):
        item = _question_to_item({"text": "Q4", "type": "checkbox", "options": ["X", "Y"]})
        assert item["questionItem"]["question"]["choiceQuestion"]["type"] == "CHECKBOX"

    def test_dropdown(self):
        item = _question_to_item({"text": "Q5", "type": "dropdown", "options": ["P", "Q"]})
        assert item["questionItem"]["question"]["choiceQuestion"]["type"] == "DROP_DOWN"

    def test_required_flag(self):
        item = _question_to_item({"text": "Q", "type": "short_answer", "required": True})
        assert item["questionItem"]["question"]["required"] is True

    def test_unsupported_type_raises(self):
        with pytest.raises(ValueError, match="Unsupported question type"):
            _question_to_item({"text": "Q", "type": "file_upload"})


class TestBuildCreateItemRequests:
    def test_builds_requests(self):
        questions = [
            {"text": "Q1", "type": "short_answer"},
            {"text": "Q2", "type": "paragraph"},
        ]
        requests = _build_create_item_requests(questions, start_index=0)
        assert len(requests) == 2
        assert requests[0]["createItem"]["location"]["index"] == 0
        assert requests[1]["createItem"]["location"]["index"] == 1

    def test_offset(self):
        requests = _build_create_item_requests([{"text": "Q1"}], start_index=5)
        assert requests[0]["createItem"]["location"]["index"] == 5


class TestExtractAnswerText:
    def test_text_answers(self):
        answer = {"textAnswers": {"answers": [{"value": "Hello"}, {"value": "World"}]}}
        assert _extract_answer_text(answer) == "Hello, World"

    def test_choice_answers(self):
        answer = {"choiceAnswers": {"answers": ["Option A", "Option B"]}}
        assert _extract_answer_text(answer) == "Option A, Option B"

    def test_file_answers(self):
        answer = {"fileUploadAnswers": {"answers": [{"fileId": "file123"}]}}
        assert _extract_answer_text(answer) == "file123"

    def test_mixed_answers(self):
        answer = {
            "textAnswers": {"answers": [{"value": "text"}]},
            "choiceAnswers": {"answers": ["choice"]},
        }
        result = _extract_answer_text(answer)
        assert "text" in result
        assert "choice" in result

    def test_empty_answer(self):
        assert _extract_answer_text({}) == ""


class TestCreateForm:
    @patch("mcp_servers.google_forms.get_service")
    def test_creates_form(self, mock_get_service):
        from mcp_servers.google_forms import create_form
        service = MagicMock()
        service.forms().create().execute.return_value = {"formId": "form123"}
        mock_get_service.return_value = service

        result = create_form("Test Form", "Description", [{"text": "Q1"}])
        assert result["form_id"] == "form123"
        assert result["title"] == "Test Form"

    @patch("mcp_servers.google_forms.get_service")
    def test_creates_form_with_auto_name(self, mock_get_service):
        from mcp_servers.google_forms import create_form
        service = MagicMock()
        service.forms().create().execute.return_value = {"formId": "form456"}
        mock_get_service.return_value = service

        result = create_form("Survey", questions=[{"text": "Email"}])
        # Should have auto-prepended Name question
        assert result["form_id"] == "form456"


class TestAddQuestionsToForm:
    def test_empty_questions_raises(self):
        from mcp_servers.google_forms import add_questions_to_form
        with pytest.raises(ValueError, match="cannot be empty"):
            add_questions_to_form("form123", [])

    @patch("mcp_servers.google_forms.get_service")
    def test_adds_questions(self, mock_get_service):
        from mcp_servers.google_forms import add_questions_to_form
        service = MagicMock()
        service.forms().get().execute.return_value = {
            "info": {"title": "Test"},
            "items": [{"title": "Q1"}],
        }
        mock_get_service.return_value = service

        result = add_questions_to_form("form123", [{"text": "New Q"}])
        assert result["added_questions"] == 1
        assert result["inserted_at"] == 1


class TestUpdateFormInfo:
    def test_no_fields_raises(self):
        from mcp_servers.google_forms import update_form_info
        with pytest.raises(ValueError, match="at least one field"):
            update_form_info("form123")

    @patch("mcp_servers.google_forms.get_service")
    def test_updates_title(self, mock_get_service):
        from mcp_servers.google_forms import update_form_info
        service = MagicMock()
        service.forms().get().execute.return_value = {
            "info": {"title": "New Title", "description": "desc"}
        }
        mock_get_service.return_value = service

        result = update_form_info("form123", title="New Title")
        assert result["title"] == "New Title"


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
