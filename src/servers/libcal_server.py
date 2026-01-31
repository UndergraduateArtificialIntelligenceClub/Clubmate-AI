from fastmcp import FastMCP
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta
import requests
import logging

mcp = FastMCP("UAlberta LibCal MCP")
logger = logging.getLogger(__name__)

API_URL = "https://ualberta.libcal.com/spaces/availability/grid"
LIBRARIES = {
    "cameron": {
        "name": "Cameron Library",
        "id": "441",
    },
    "sperber": {
        "name": "Sperber Library",
        "id": "2950",
    },
}

# Class name mappings (from API response)
# empty className or unrecognized values are treated as Available
STATUS_MAP = {
    "s-lc-eq-avail": "Available",
    "s-lc-eq-checkout": "Checked Out",
    "s-lc-eq-pending": "Pending",
    "": "Available",  # Empty className = available
}

# Room mappings (itemId -> room name) - scraped via Playwright
ROOM_MAPPINGS = {
    "cameron": {
        5574: "ROOM 1-21",
        3420: "ROOM 1-22",
        3421: "ROOM 1-24",
        3422: "ROOM 1-25",
        3423: "ROOM 1-26",
        3424: "ROOM 1-27",
        5575: "ROOM 1-28",
        3782: "ROOM B-05A",
        3786: "ROOM B-05B",
        5577: "ROOM B-05C",
        5578: "ROOM B-05D",
        5579: "ROOM B-05E",
        5580: "ROOM B-05F",
        5581: "ROOM B-05G",
        5582: "ROOM B-05H",
        5583: "ROOM B-05J",
        3784: "ROOM B-14A",
        3785: "ROOM B-14B",
    },
    "sperber": {},
}


def fetch_availability(library_key: str, date: str = None) -> Optional[Dict]:
    """
    Fetch availability for a specific library from the LibCal API.

    Args:
        library_key: Key from LIBRARIES dict (e.g., "cameron")
        date: Date string in YYYY-MM-DD format (defaults to today)

    Returns:
        API response dict or None on failure
    """
    if library_key not in LIBRARIES:
        return None

    library = LIBRARIES[library_key]

    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    start_date = datetime.strptime(date, "%Y-%m-%d")
    end_date = start_date + timedelta(days=1)

    session = requests.Session()
    session.get("https://ualberta.libcal.com/allspaces", headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    })

    payload = {
        "lid": library["id"],
        "gid": 0,
        "eid": -1,
        "seat": 0,
        "seatId": 0,
        "zone": 0,
        "start": start_date.strftime("%Y-%m-%d"),
        "end": end_date.strftime("%Y-%m-%d"),
        "pageIndex": 0,
        "pageSize": 18,
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "https://ualberta.libcal.com/allspaces",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://ualberta.libcal.com",
    }

    try:
        response = session.post(API_URL, data=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None


def parse_slots(data: Dict, library_key: str) -> Dict[str, list]:
    """Parse API response and categorize slots by status with room names."""
    if not data or "slots" not in data:
        return {}

    room_mapping = ROOM_MAPPINGS.get(library_key, {})
    categorized = {}

    for slot in data["slots"]:
        status_class = slot.get("className", "")
        # Default unknown classNames to Available (most unbooked slots have no special class)
        status = STATUS_MAP.get(status_class, "Available")

        if status not in categorized:
            categorized[status] = []

        item_id = slot["itemId"]
        room_name = room_mapping.get(item_id, f"Unknown ({item_id})")

        
        start_time = slot["start"].split("T")[1][:5] if "T" in slot["start"] else slot["start"].split(" ")[1][:5] if " " in slot["start"] else slot["start"]
        end_time = slot["end"].split("T")[1][:5] if "T" in slot["end"] else slot["end"].split(" ")[1][:5] if " " in slot["end"] else slot["end"]

        categorized[status].append({
            "room": room_name,
            "item_id": item_id,
            "start": start_time,
            "end": end_time,
        })

    return categorized


def format_results(results: Dict[str, Any]) -> str:
    """
    Format availability results into a human-readable string.

    Args:
        results: Dictionary containing availability results

    Returns:
        Formatted string with availability information for Discord.
        Consecutive slots are merged (e.g., 18:30-19:00, 19:00-19:30 -> 6:30 PM - 7:30 PM).
        Military time is converted to standard time.
    """
    if "error" in results:
        return f"Error: {results['error']}"

    def to_standard_time(military: str) -> str:
        """Convert 24h time (HH:MM) to 12h format."""
        hour, minute = int(military[:2]), military[3:5]
        period = "AM" if hour < 12 else "PM"
        if hour == 0:
            hour = 12
        elif hour > 12:
            hour -= 12
        return f"{hour}:{minute} {period}"

    def merge_consecutive_slots(slots: list[str]) -> list[str]:
        """Merge consecutive time slots."""
        if not slots:
            return []

        parsed = []
        for slot in slots:
            start, end = slot.split("-")
            parsed.append((start, end))

        parsed.sort(key=lambda x: x[0])

        merged = [parsed[0]]
        for start, end in parsed[1:]:
            if start == merged[-1][1]:
                merged[-1] = (merged[-1][0], end)
            else:
                merged.append((start, end))

        return [f"{to_standard_time(s)} - {to_standard_time(e)}" for s, e in merged]

    date_str = results.get("date", "")
    if date_str:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%A, %B %d, %Y")
    else:
        formatted_date = "Unknown date"

    # Build time filter string if present
    time_filter = results.get("time_filter")
    time_filter_str = ""
    if time_filter:
        start = to_standard_time(time_filter["start"]) if time_filter.get("start") else None
        end = to_standard_time(time_filter["end"]) if time_filter.get("end") else None
        if start and end:
            time_filter_str = f" ({start} - {end})"
        elif start:
            time_filter_str = f" (after {start})"
        elif end:
            time_filter_str = f" (before {end})"

    lines = [
        f"**{results['library']} - Room Availability**",
        f"{formatted_date}{time_filter_str}",
        "",
    ]

    available_by_room = results.get("available_by_room", {})
    if not available_by_room:
        lines.append("No rooms available.")
    else:
        for room in sorted(available_by_room.keys()):
            slots = available_by_room[room]
            merged = merge_consecutive_slots(slots)
            times_str = ", ".join(merged) if merged else "None"
            lines.append(f"**{room}**")
            lines.append(f"  {times_str}")

    lines.append("")
    lines.append(f"_{results.get('total_available_slots', 0)} total slots_")

    return "\n".join(lines)


@mcp.tool()
def get_available_slots(
    location: str,
    date: Optional[str] = None,
    room_filter: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    formatted: bool = True
) -> Union[Dict[str, Any], str]:
    """
    Get available study room time slots for a specific UAlberta library.

    NOTE to model:
        Remind the user that the booking website books per 30 minute time slots. Send them to the website as well if they want to book
        a time slot as we can't book for them due to restrictions on the website. 
        https://libcal.ualberta.ca/

    Args:
        location: Library identifier. One of: cameron, sperber
        date: Optional date in YYYY-MM-DD format (defaults to today)
        room_filter: Optional - filter by room name (partial match)
        start_time: Optional - filter slots starting at or after this time (HH:MM, 24h format, e.g. "17:00" for 5 PM)
        end_time: Optional - filter slots ending at or before this time (HH:MM, 24h format, e.g. "19:00" for 7 PM)
        formatted: If True, returns a human-readable string. If False, returns raw dict.

    Returns:
        Formatted string (default) or dict with available_slots grouped by room
    """
    location_key = location.lower().strip()

    if location_key not in LIBRARIES:
        error_result = {"error": f"Unknown library '{location}'. Valid options: {', '.join(LIBRARIES.keys())}"}
        return format_results(error_result) if formatted else error_result

    library_info = LIBRARIES[location_key]

    try:
        data = fetch_availability(location_key, date)

        if not data:
            error_result = {"error": f"Failed to fetch data for {library_info['name']}"}
            return format_results(error_result) if formatted else error_result

        categorized = parse_slots(data, location_key)

        # Get available slots
        available = categorized.get("Available", [])

        # Filter by time range if specified
        if start_time or end_time:
            filtered = []
            for slot in available:
                slot_start = slot["start"]
                slot_end = slot["end"]
                # Include slot if it overlaps with the requested range
                if start_time and slot_end <= start_time:
                    continue
                if end_time and slot_start >= end_time:
                    continue
                filtered.append(slot)
            available = filtered

        # Group by room
        by_room = {}
        for slot in available:
            room = slot["room"]
            if room_filter and room_filter.lower() not in room.lower():
                continue
            if room not in by_room:
                by_room[room] = []
            by_room[room].append(f"{slot['start']}-{slot['end']}")

        results = {
            "library": library_info["name"],
            "location": location_key,
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "time_filter": {"start": start_time, "end": end_time} if (start_time or end_time) else None,
            "available_by_room": by_room,
            "total_available_slots": len(available),
            "message": f"Found {len(available)} available slots at {library_info['name']}"
        }

        return format_results(results) if formatted else results

    except Exception as e:
        logger.error(f"Failed to get availability: {e}")
        error_result = {"error": f"Failed to get availability for {library_info['name']}: {str(e)}"}
        return format_results(error_result) if formatted else error_result


@mcp.tool()
def list_libraries() -> Dict[str, Any]:
    """
    List all available UAlberta library locations that can be queried.

    Returns:
        dict with list of libraries and their identifiers
    """
    libraries_list = [
        {"id": key, "name": info["name"]}
        for key, info in LIBRARIES.items()
    ]

    return {
        "libraries": libraries_list,
        "message": "Use these location IDs with get_available_slots"
    }

if __name__ == "__main__":
    mcp.run()
