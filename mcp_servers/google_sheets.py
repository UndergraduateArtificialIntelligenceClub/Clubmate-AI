"""
Google Sheets MCP Server for Clubmate AI.
Provides tools to read, write, and append data to Google Sheets.
"""

import logging
import sys
from pathlib import Path
from typing import List, Optional

from fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mcp_servers.google_auth import get_service

logger = logging.getLogger(__name__)
mcp = FastMCP("Google Sheets")


def _extract_sheet_id(url_or_id: str) -> str:
    """Extract spreadsheet ID from a Google Sheets URL or return as-is."""
    if "spreadsheets" in url_or_id:
        parts = url_or_id.split("/d/")
        if len(parts) > 1:
            return parts[1].split("/")[0]
    return url_or_id


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def read_sheet(
    sheet_url_or_id: str,
    range_notation: str = "Sheet1",
) -> dict:
    """
    Read data from a Google Sheet.

    Args:
        sheet_url_or_id: Google Sheets URL or spreadsheet ID
        range_notation: Sheet range in A1 notation (e.g. 'Sheet1', 'Sheet1!A1:D10')
    """
    sheet_id = _extract_sheet_id(sheet_url_or_id)
    service = get_service("sheets", "v4")
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=sheet_id, range=range_notation)
        .execute()
    )
    values = result.get("values", [])
    return {
        "spreadsheet_id": sheet_id,
        "range": result.get("range", range_notation),
        "rows": values,
        "row_count": len(values),
    }


@mcp.tool()
def append_rows(
    sheet_url_or_id: str,
    rows: List[List[str]],
    sheet_name: str = "Sheet1",
) -> dict:
    """
    Append rows of data to the end of a Google Sheet.

    Args:
        sheet_url_or_id: Google Sheets URL or spreadsheet ID
        rows: List of rows, each row is a list of cell values (e.g. [['Alice', '25'], ['Bob', '30']])
        sheet_name: Name of the sheet tab (default: 'Sheet1')
    """
    sheet_id = _extract_sheet_id(sheet_url_or_id)
    service = get_service("sheets", "v4")
    result = (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=sheet_id,
            range=sheet_name,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": rows},
        )
        .execute()
    )
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
    updates = result.get("updates", {})
    logger.info("Appended %d rows to sheet %s", len(rows), sheet_id)
    return {
        "spreadsheet_id": sheet_id,
        "updated_range": updates.get("updatedRange", ""),
        "rows_added": len(rows),
        "message": f"Added {len(rows)} row(s) to sheet. {url}",
        "url": url,
    }


@mcp.tool()
def write_range(
    sheet_url_or_id: str,
    range_notation: str,
    values: List[List[str]],
) -> dict:
    """
    Write data to a specific range in a Google Sheet (overwrites existing data).

    Args:
        sheet_url_or_id: Google Sheets URL or spreadsheet ID
        range_notation: Target range in A1 notation (e.g. 'Sheet1!A1:C3')
        values: 2D list of values to write
    """
    sheet_id = _extract_sheet_id(sheet_url_or_id)
    service = get_service("sheets", "v4")
    result = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=sheet_id,
            range=range_notation,
            valueInputOption="USER_ENTERED",
            body={"values": values},
        )
        .execute()
    )
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
    logger.info("Wrote to range %s in sheet %s", range_notation, sheet_id)
    return {
        "spreadsheet_id": sheet_id,
        "updated_range": result.get("updatedRange", range_notation),
        "cells_updated": result.get("updatedCells", 0),
        "message": f"Wrote to {range_notation}. {url}",
        "url": url,
    }


@mcp.tool()
def create_spreadsheet(title: str) -> dict:
    """
    Create a new Google Spreadsheet.

    Args:
        title: Title of the new spreadsheet
    """
    service = get_service("sheets", "v4")
    sheet = (
        service.spreadsheets()
        .create(body={"properties": {"title": title}})
        .execute()
    )
    sheet_id = sheet.get("spreadsheetId")
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
    logger.info("Created spreadsheet: %s (%s)", title, sheet_id)
    return {
        "spreadsheet_id": sheet_id,
        "title": title,
        "url": url,
        "message": f"Spreadsheet '{title}' created. {url}",
    }


if __name__ == "__main__":
    mcp.run()
