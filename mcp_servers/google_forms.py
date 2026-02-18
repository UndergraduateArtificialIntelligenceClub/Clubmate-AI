"""
Google Forms MCP Server for Clubmate AI.
Provides tools to create forms and retrieve responses.
"""

import logging
import sys
from pathlib import Path
from typing import List, Optional

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

    # Add questions if provided
    if questions:
        requests = []
        for i, q in enumerate(questions):
            q_type = q.get("type", "short_answer")
            required = q.get("required", False)

            question_item = {
                "title": q["text"],
                "questionItem": {},
            }

            if q_type == "short_answer":
                question_item["questionItem"]["question"] = {
                    "required": required,
                    "textQuestion": {"paragraph": False},
                }
            elif q_type == "paragraph":
                question_item["questionItem"]["question"] = {
                    "required": required,
                    "textQuestion": {"paragraph": True},
                }
            elif q_type in ("multiple_choice", "checkbox", "dropdown"):
                type_map = {
                    "multiple_choice": "RADIO",
                    "checkbox": "CHECKBOX",
                    "dropdown": "DROP_DOWN",
                }
                options = q.get("options", [])
                question_item["questionItem"]["question"] = {
                    "required": required,
                    "choiceQuestion": {
                        "type": type_map[q_type],
                        "options": [{"value": opt} for opt in options],
                    },
                }

            requests.append({
                "createItem": {
                    "item": question_item,
                    "location": {"index": i},
                }
            })

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
        "message": f"Form '{title}' created with {len(questions or [])} question(s). Share this link for responses: {respond_url}",
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
    for r in responses:
        row = {"response_id": r.get("responseId"), "submitted_at": r.get("createTime")}
        for q_id, answer in r.get("answers", {}).items():
            q_title = question_map.get(q_id, q_id)
            text_answers = answer.get("textAnswers", {}).get("answers", [])
            row[q_title] = ", ".join(a.get("value", "") for a in text_answers)
        parsed.append(row)

    logger.info("Retrieved %d responses from form %s", len(parsed), form_id)
    return {
        "form_id": form_id,
        "form_title": title,
        "total_responses": len(parsed),
        "responses": parsed,
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
