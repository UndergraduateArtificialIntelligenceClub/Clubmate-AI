"""
Google Forms MCP Server for Clubmate AI.
Provides tools to create forms and retrieve responses.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mcp_servers.google_auth import get_service

logger = logging.getLogger(__name__)
mcp = FastMCP("Google Forms")


def _extract_form_id(url_or_id: str) -> str:
    """Extract form ID from a Google Forms URL or return as-is."""
    if "forms.google.com" in url_or_id or "docs.google.com/forms" in url_or_id:
        # URL format: https://docs.google.com/forms/d/FORM_ID/edit
        parts = url_or_id.split("/d/")
        if len(parts) > 1:
            return parts[1].split("/")[0]
    return url_or_id


def _looks_like_name_question(text: str) -> bool:
    """Heuristic for identifying a name field."""
    normalized = text.strip().lower()
    return "name" in normalized


def _ensure_name_question(questions: Optional[List[dict]]) -> List[dict]:
    """
    Ensure forms capture respondent identity.
    If no name-style question exists, prepend a required "Name" field.
    """
    prepared = list(questions or [])
    has_name = any(_looks_like_name_question(str(q.get("text", ""))) for q in prepared)
    if not has_name:
        prepared.insert(0, {"text": "Name", "type": "short_answer", "required": True})
    return prepared


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def create_form(
    title: str,
    description: Optional[str] = None,
    questions: Optional[List[dict]] = None,
) -> dict:
    """
    Create a new Google Form.

    Args:
        title: Form title
        description: Optional form description
        questions: Optional list of questions. Each question is a dict with:
            - 'text': Question text (required)
            - 'type': 'short_answer', 'paragraph', 'multiple_choice', 'checkbox', 'dropdown' (default: 'short_answer')
            - 'required': bool (default: False)
            - 'options': List of option strings (for multiple_choice, checkbox, dropdown)

    Example questions:
        [
            {"text": "Your name?", "type": "short_answer", "required": True},
            {"text": "Dietary restrictions?", "type": "multiple_choice", "options": ["None", "Vegetarian", "Vegan", "Halal"]},
        ]
    """
    service = get_service("forms", "v1")

    # Create the base form
    form_body = {"info": {"title": title}}
    if description:
        form_body["info"]["description"] = description

    form = service.forms().create(body=form_body).execute()
    form_id = form.get("formId")

    prepared_questions = _ensure_name_question(questions)

    # Add questions
    if prepared_questions:
        requests = _build_create_item_requests(prepared_questions, start_index=0)

        if requests:
            service.forms().batchUpdate(
                formId=form_id, body={"requests": requests}
            ).execute()

    url = f"https://docs.google.com/forms/d/{form_id}/edit"
    respond_url = f"https://docs.google.com/forms/d/{form_id}/viewform"
    logger.info("Created form: %s (%s)", title, form_id)
    return {
        "form_id": form_id,
        "title": title,
        "edit_url": url,
        "respond_url": respond_url,
        "message": (
            f"Form '{title}' created with {len(prepared_questions)} question(s), "
            f"including a Name field for respondent identity. "
            f"Share this link for responses: {respond_url}"
        ),
    }


def _question_to_item(question: dict) -> dict:
    """Convert a question payload into a Google Forms item."""
    q_type = question.get("type", "short_answer")
    required = question.get("required", False)

    item = {
        "title": question["text"],
        "questionItem": {},
    }

    if q_type == "short_answer":
        item["questionItem"]["question"] = {
            "required": required,
            "textQuestion": {"paragraph": False},
        }
    elif q_type == "paragraph":
        item["questionItem"]["question"] = {
            "required": required,
            "textQuestion": {"paragraph": True},
        }
    elif q_type in ("multiple_choice", "checkbox", "dropdown"):
        type_map = {
            "multiple_choice": "RADIO",
            "checkbox": "CHECKBOX",
            "dropdown": "DROP_DOWN",
        }
        options = question.get("options", [])
        item["questionItem"]["question"] = {
            "required": required,
            "choiceQuestion": {
                "type": type_map[q_type],
                "options": [{"value": opt} for opt in options],
            },
        }
    else:
        raise ValueError(
            f"Unsupported question type '{q_type}'. "
            "Use one of: short_answer, paragraph, multiple_choice, checkbox, dropdown."
        )

    return item


def _build_create_item_requests(questions: List[dict], start_index: int) -> List[dict]:
    """Build createItem requests for batchUpdate."""
    requests: List[dict] = []
    for offset, question in enumerate(questions):
        requests.append(
            {
                "createItem": {
                    "item": _question_to_item(question),
                    "location": {"index": start_index + offset},
                }
            }
        )
    return requests


def _extract_answer_text(answer: dict) -> str:
    """Extract a human-readable answer from a Google Forms answer payload."""
    values: List[str] = []

    text_answers = answer.get("textAnswers", {}).get("answers", [])
    values.extend(a.get("value", "") for a in text_answers if a.get("value"))

    choice_answers = answer.get("choiceAnswers", {}).get("answers", [])
    values.extend(a for a in choice_answers if a)

    file_answers = answer.get("fileUploadAnswers", {}).get("answers", [])
    values.extend(a.get("fileId", "") for a in file_answers if a.get("fileId"))

    return ", ".join(values).strip()


def _form_metadata(service, form_id: str) -> Tuple[str, int]:
    """Return (title, current_question_count)."""
    form = service.forms().get(formId=form_id).execute()
    title = form.get("info", {}).get("title", "Untitled Form")
    count = len(form.get("items", []))
    return title, count


@mcp.tool()
def add_questions_to_form(
    form_url_or_id: str,
    questions: List[dict],
    insert_at: Optional[int] = None,
) -> dict:
    """
    Add one or more questions to an existing Google Form.

    Args:
        form_url_or_id: Google Forms URL or form ID.
        questions: List of question dicts (same schema as create_form()).
        insert_at: Optional question index to insert at. Defaults to append.
    """
    if not questions:
        raise ValueError("questions cannot be empty")

    form_id = _extract_form_id(form_url_or_id)
    service = get_service("forms", "v1")
    title, count = _form_metadata(service, form_id)

    start_index = count if insert_at is None else max(0, insert_at)
    requests = _build_create_item_requests(questions, start_index=start_index)

    service.forms().batchUpdate(
        formId=form_id,
        body={"requests": requests},
    ).execute()

    logger.info(
        "Added %d question(s) to form %s at index %d",
        len(questions),
        form_id,
        start_index,
    )
    return {
        "form_id": form_id,
        "title": title,
        "added_questions": len(questions),
        "inserted_at": start_index,
        "edit_url": f"https://docs.google.com/forms/d/{form_id}/edit",
        "respond_url": f"https://docs.google.com/forms/d/{form_id}/viewform",
        "message": f"Added {len(questions)} question(s) to '{title}'.",
    }


@mcp.tool()
def update_form_info(
    form_url_or_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
) -> dict:
    """
    Update an existing Google Form's title and/or description.

    Args:
        form_url_or_id: Google Forms URL or form ID.
        title: New form title (optional).
        description: New form description (optional).
    """
    if title is None and description is None:
        raise ValueError("Provide at least one field to update: title and/or description.")

    form_id = _extract_form_id(form_url_or_id)
    service = get_service("forms", "v1")

    info = {}
    mask_parts: List[str] = []
    if title is not None:
        info["title"] = title
        mask_parts.append("title")
    if description is not None:
        info["description"] = description
        mask_parts.append("description")

    service.forms().batchUpdate(
        formId=form_id,
        body={
            "requests": [
                {
                    "updateFormInfo": {
                        "info": info,
                        "updateMask": ",".join(mask_parts),
                    }
                }
            ]
        },
    ).execute()

    logger.info("Updated form info for %s (fields: %s)", form_id, ",".join(mask_parts))
    refreshed = service.forms().get(formId=form_id).execute()
    new_title = refreshed.get("info", {}).get("title", "Untitled Form")
    new_description = refreshed.get("info", {}).get("description", "")
    return {
        "form_id": form_id,
        "title": new_title,
        "description": new_description,
        "edit_url": f"https://docs.google.com/forms/d/{form_id}/edit",
        "respond_url": f"https://docs.google.com/forms/d/{form_id}/viewform",
        "message": f"Updated form info for '{new_title}'.",
    }


@mcp.tool()
def get_form_responses(form_url_or_id: str) -> dict:
    """
    Retrieve all responses from a Google Form.

    Args:
        form_url_or_id: Google Forms URL or form ID
    """
    form_id = _extract_form_id(form_url_or_id)
    service = get_service("forms", "v1")

    # Get form metadata for question titles
    form = service.forms().get(formId=form_id).execute()
    title = form.get("info", {}).get("title", "Untitled Form")

    # Map question IDs to their titles
    question_map = {}
    for item in form.get("items", []):
        q = item.get("questionItem", {}).get("question", {})
        if q:
            question_map[q.get("questionId", "")] = item.get("title", "Question")

    # Get responses
    responses_result = service.forms().responses().list(formId=form_id).execute()
    responses = responses_result.get("responses", [])

    parsed = []
    by_user = []
    for idx, r in enumerate(responses, start=1):
        row = {
            "response_id": r.get("responseId"),
            "submitted_at": r.get("createTime"),
            "respondent_email": r.get("respondentEmail"),
        }
        answers: Dict[str, str] = {}
        for q_id, answer in r.get("answers", {}).items():
            q_title = question_map.get(q_id, q_id)
            answer_text = _extract_answer_text(answer)
            row[q_title] = answer_text
            answers[q_title] = answer_text

        respondent_name = None
        for question_title, value in answers.items():
            if _looks_like_name_question(question_title) and value:
                respondent_name = value
                break

        respondent = respondent_name or row.get("respondent_email") or f"Respondent {idx}"
        row["respondent_name"] = respondent_name
        row["respondent"] = respondent
        parsed.append(row)
        by_user.append(
            {
                "respondent": respondent,
                "respondent_name": respondent_name,
                "respondent_email": row.get("respondent_email"),
                "answers": answers,
            }
        )

    logger.info("Retrieved %d responses from form %s", len(parsed), form_id)
    return {
        "form_id": form_id,
        "form_title": title,
        "total_responses": len(parsed),
        "responses": parsed,
        "responses_by_user": by_user,
        "identity_note": (
            "Respondent names come from a Name question. "
            "If absent, respondent email is used when available."
        ),
    }


@mcp.tool()
def get_form_info(form_url_or_id: str) -> dict:
    """
    Get metadata and question list for a Google Form.

    Args:
        form_url_or_id: Google Forms URL or form ID
    """
    form_id = _extract_form_id(form_url_or_id)
    service = get_service("forms", "v1")
    form = service.forms().get(formId=form_id).execute()

    title = form.get("info", {}).get("title", "Untitled")
    description = form.get("info", {}).get("description", "")
    items = [
        {"title": item.get("title", ""), "type": list(item.keys())}
        for item in form.get("items", [])
    ]

    respond_url = f"https://docs.google.com/forms/d/{form_id}/viewform"
    return {
        "form_id": form_id,
        "title": title,
        "description": description,
        "question_count": len(items),
        "questions": items,
        "respond_url": respond_url,
    }


if __name__ == "__main__":
    mcp.run()
