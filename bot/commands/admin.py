"""
Exec-only slash commands for Clubmate AI.
Requires the configured exec role (set in dashboard → Permissions).
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from bot.permissions import exec_only
from config import settings

logger = logging.getLogger(__name__)
ADMIN_CHAT_TIMEOUT = 90  # seconds
ADMIN_CALENDAR_TIMEOUT = 60  # seconds


async def _wait_for_prewarm(bot):
    """Wait for the bot's pre-warm task before handling commands."""
    task = getattr(bot, '_prewarm_task', None)
    if task and not task.done():
        await task


async def _chat_with_timeout(client, prompt: str) -> str:
    """Run admin tool-style prompts without RAG context and with a hard timeout."""
    try:
        return await asyncio.wait_for(
            client.chat(prompt, include_rag=False),
            timeout=ADMIN_CHAT_TIMEOUT,
        )
    except asyncio.TimeoutError:
        return "⏱️ Timed out while waiting on calendar/tools. Please try again."
    except Exception as e:
        logger.error("Admin chat error: %s", e)
        return f"❌ Something went wrong: {e}"


def _time_for_date(date: str, time_or_iso: str) -> str:
    """
    Accept HH:MM / HH:MM:SS / full datetime and normalize to an ISO-like value
    suitable for calendar reschedule calls.
    """
    value = time_or_iso.strip()
    if "T" in value:
        return value
    if len(value) == 5:
        return f"{date}T{value}:00"
    if len(value) == 8:
        return f"{date}T{value}"
    return value


def _format_day_schedule(result: dict) -> str:
    if "error" in result:
        return f"❌ {result['error']}"
    if not result.get("events"):
        return result.get("message", "No events found.")

    lines = [
        f"**Schedule for {result.get('date')}** ({result.get('timezone')})",
    ]
    for event in result["events"]:
        attendees = event.get("attendees") or []
        attendee_text = f" | 👥 {len(attendees)} attendee(s)" if attendees else ""
        lines.append(
            f"- `{event.get('start')} → {event.get('end')}` — **{event.get('summary', 'No Title')}**{attendee_text}"
        )
    return "\n".join(lines)


def _format_calendar_result(result: dict) -> str:
    if "error" in result:
        meetings = result.get("meetings") or []
        if meetings:
            options = "\n".join(
                f"- {m.get('summary')} ({m.get('start')} → {m.get('end')})"
                for m in meetings
            )
            return f"❌ {result['error']}\n\nMatches found:\n{options}"
        return f"❌ {result['error']}"
    return result.get("message", str(result))

try:
    from bot.events.on_voice import start_meeting, end_meeting
    VOICE_AVAILABLE = True
except ImportError as e:
    logger.warning("Voice/meeting features disabled: %s", e)
    VOICE_AVAILABLE = False


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot, session_manager):
        self.bot = bot
        self.sessions = session_manager

    # ── Calendar ──────────────────────────────────────────────────────────────

    @app_commands.command(name="schedule", description="Schedule a meeting on Google Calendar")
    @app_commands.describe(
        details="Describe the meeting — time, attendees, title (e.g. 'Schedule a team meeting tomorrow at 3pm with alice@example.com')"
    )
    @exec_only()
    async def schedule(self, interaction: discord.Interaction, details: str):
        await interaction.response.defer(thinking=True)
        await _wait_for_prewarm(self.bot)
        client = await self.sessions.get(interaction.channel_id)
        response = await _chat_with_timeout(client, f"Schedule a meeting: {details}")
        await interaction.followup.send(response)

    @app_commands.command(name="cancel-meeting", description="Cancel a meeting on Google Calendar")
    @app_commands.describe(details="Meeting name and date to cancel")
    @exec_only()
    async def cancel_meeting(self, interaction: discord.Interaction, details: str):
        await interaction.response.defer(thinking=True)
        await _wait_for_prewarm(self.bot)
        client = await self.sessions.get(interaction.channel_id)
        response = await _chat_with_timeout(client, f"Cancel this meeting: {details}")
        await interaction.followup.send(response)

    @app_commands.command(name="reschedule", description="Reschedule a meeting")
    @app_commands.describe(details="Meeting name, current date, and new time")
    @exec_only()
    async def reschedule(self, interaction: discord.Interaction, details: str):
        await interaction.response.defer(thinking=True)
        await _wait_for_prewarm(self.bot)
        client = await self.sessions.get(interaction.channel_id)
        response = await _chat_with_timeout(client, f"Reschedule this meeting: {details}")
        await interaction.followup.send(response)

    @app_commands.command(name="invite", description="Add members to an existing meeting")
    @app_commands.describe(details="Meeting name/date and email addresses to add")
    @exec_only()
    async def invite(self, interaction: discord.Interaction, details: str):
        await interaction.response.defer(thinking=True)
        await _wait_for_prewarm(self.bot)
        client = await self.sessions.get(interaction.channel_id)
        response = await _chat_with_timeout(client, f"Add these people to the meeting: {details}")
        await interaction.followup.send(response)

    @app_commands.command(name="day-schedule", description="List all meetings on a specific date")
    @app_commands.describe(date="Date in YYYY-MM-DD format")
    @exec_only()
    async def day_schedule(self, interaction: discord.Interaction, date: str):
        await interaction.response.defer(thinking=True)
        await _wait_for_prewarm(self.bot)
        try:
            from mcp_servers.google_calendar import list_events_on_date
            result = await asyncio.wait_for(
                asyncio.to_thread(list_events_on_date, date),
                timeout=ADMIN_CALENDAR_TIMEOUT,
            )
            await interaction.followup.send(_format_day_schedule(result))
        except asyncio.TimeoutError:
            await interaction.followup.send("⏱️ Timed out while fetching that day's schedule.")
        except Exception as e:
            logger.error("day-schedule failed: %s", e)
            await interaction.followup.send(f"❌ Could not fetch schedule for {date}: {e}")

    @app_commands.command(name="cancel-day", description="Cancel a meeting by name on a given day")
    @app_commands.describe(
        date="Date in YYYY-MM-DD format",
        meeting_name="Meeting title (or part of it)",
    )
    @exec_only()
    async def cancel_day(self, interaction: discord.Interaction, date: str, meeting_name: str):
        await interaction.response.defer(thinking=True)
        await _wait_for_prewarm(self.bot)
        try:
            from mcp_servers.google_calendar import cancel_meeting
            result = await asyncio.wait_for(
                asyncio.to_thread(cancel_meeting, None, meeting_name, date),
                timeout=ADMIN_CALENDAR_TIMEOUT,
            )
            await interaction.followup.send(_format_calendar_result(result))
        except asyncio.TimeoutError:
            await interaction.followup.send("⏱️ Timed out while cancelling the meeting.")
        except Exception as e:
            logger.error("cancel-day failed: %s", e)
            await interaction.followup.send(f"❌ Could not cancel the meeting: {e}")

    @app_commands.command(name="reschedule-day", description="Reschedule a meeting found by date + name")
    @app_commands.describe(
        date="Original meeting date (YYYY-MM-DD)",
        meeting_name="Meeting title (or part of it)",
        new_start_time="New start time (HH:MM or YYYY-MM-DDTHH:MM:SS)",
        new_end_time="New end time (HH:MM or YYYY-MM-DDTHH:MM:SS)",
    )
    @exec_only()
    async def reschedule_day(
        self,
        interaction: discord.Interaction,
        date: str,
        meeting_name: str,
        new_start_time: str,
        new_end_time: str,
    ):
        await interaction.response.defer(thinking=True)
        await _wait_for_prewarm(self.bot)
        try:
            from mcp_servers.google_calendar import reschedule_meeting
            start_value = _time_for_date(date, new_start_time)
            end_value = _time_for_date(date, new_end_time)
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    reschedule_meeting,
                    start_value,
                    end_value,
                    None,
                    meeting_name,
                    date,
                ),
                timeout=ADMIN_CALENDAR_TIMEOUT,
            )
            await interaction.followup.send(_format_calendar_result(result))
        except asyncio.TimeoutError:
            await interaction.followup.send("⏱️ Timed out while rescheduling the meeting.")
        except Exception as e:
            logger.error("reschedule-day failed: %s", e)
            await interaction.followup.send(f"❌ Could not reschedule the meeting: {e}")

    @app_commands.command(name="invite-day", description="Add attendees to a meeting found by date + name")
    @app_commands.describe(
        date="Meeting date (YYYY-MM-DD)",
        meeting_name="Meeting title (or part of it)",
        attendees="Comma-separated email addresses",
    )
    @exec_only()
    async def invite_day(
        self,
        interaction: discord.Interaction,
        date: str,
        meeting_name: str,
        attendees: str,
    ):
        await interaction.response.defer(thinking=True)
        await _wait_for_prewarm(self.bot)
        try:
            from mcp_servers.google_calendar import add_invites
            emails = [email.strip() for email in attendees.split(",") if email.strip()]
            if not emails:
                await interaction.followup.send("❌ Please provide at least one attendee email.")
                return

            result = await asyncio.wait_for(
                asyncio.to_thread(add_invites, emails, None, meeting_name, date),
                timeout=ADMIN_CALENDAR_TIMEOUT,
            )
            await interaction.followup.send(_format_calendar_result(result))
        except asyncio.TimeoutError:
            await interaction.followup.send("⏱️ Timed out while adding invites.")
        except Exception as e:
            logger.error("invite-day failed: %s", e)
            await interaction.followup.send(f"❌ Could not add invites: {e}")

    # ── Docs / Sheets / Forms ─────────────────────────────────────────────────

    @app_commands.command(name="create-doc", description="Create a new Google Document")
    @app_commands.describe(details="Document title and optional initial content")
    @exec_only()
    async def create_doc(self, interaction: discord.Interaction, details: str):
        await interaction.response.defer(thinking=True)
        await _wait_for_prewarm(self.bot)
        client = await self.sessions.get(interaction.channel_id)
        response = await _chat_with_timeout(client, f"Create a Google Doc: {details}")
        await interaction.followup.send(response)

    @app_commands.command(name="create-form", description="Create a Google Form")
    @app_commands.describe(details="Describe the form — title, purpose, and questions to include")
    @exec_only()
    async def create_form(self, interaction: discord.Interaction, details: str):
        await interaction.response.defer(thinking=True)
        await _wait_for_prewarm(self.bot)
        client = await self.sessions.get(interaction.channel_id)
        response = await _chat_with_timeout(client, f"Create a Google Form: {details}")
        await interaction.followup.send(response)

    @app_commands.command(name="form-responses", description="Get responses from a Google Form")
    @app_commands.describe(form_url="Google Form URL or ID")
    @exec_only()
    async def form_responses(self, interaction: discord.Interaction, form_url: str):
        await interaction.response.defer(thinking=True)
        await _wait_for_prewarm(self.bot)
        client = await self.sessions.get(interaction.channel_id)
        response = await _chat_with_timeout(client, f"Get responses from this form: {form_url}")
        await interaction.followup.send(response)

    @app_commands.command(name="read-sheet", description="Read data from a Google Sheet")
    @app_commands.describe(
        sheet_url="Google Sheets URL or ID",
        range_notation="Optional range (e.g. Sheet1!A1:D10)"
    )
    @exec_only()
    async def read_sheet(
        self,
        interaction: discord.Interaction,
        sheet_url: str,
        range_notation: str = "Sheet1",
    ):
        await interaction.response.defer(thinking=True)
        await _wait_for_prewarm(self.bot)
        client = await self.sessions.get(interaction.channel_id)
        response = await _chat_with_timeout(
            client,
            f"Read data from this sheet: {sheet_url}, range: {range_notation}"
        )
        await interaction.followup.send(response)

    # ── Knowledge Base ────────────────────────────────────────────────────────

    @app_commands.command(name="ingest", description="Add a document or Google Doc to the knowledge base")
    @app_commands.describe(source="File path on server or Google Doc URL")
    @exec_only()
    async def ingest(self, interaction: discord.Interaction, source: str):
        await interaction.response.defer(thinking=True)
        await _wait_for_prewarm(self.bot)
        client = await self.sessions.get(interaction.channel_id)

        if not client.rag_available():
            await interaction.followup.send("RAG module is not available.")
            return

        # Google Doc URL → fetch content and ingest
        if "docs.google.com" in source:
            response = await client.chat(
                f"Read this Google Doc and I'll tell you what to do next: {source}"
            )
            await interaction.followup.send(
                "To ingest a Google Doc, use the dashboard → Knowledge Base page to sync it directly."
            )
            return

        # Local file path
        path = Path(source)
        if not path.exists():
            await interaction.followup.send(f"Path not found: `{source}`")
            return

        success = await client.ingest(str(path))
        if success:
            await interaction.followup.send(f"Ingested `{source}` into the knowledge base.")
        else:
            await interaction.followup.send(f"Ingestion failed or no documents found at `{source}`.")

    @app_commands.command(name="kb-reset", description="Clear the entire knowledge base")
    @exec_only()
    async def kb_reset(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        await _wait_for_prewarm(self.bot)
        client = await self.sessions.get(interaction.channel_id)
        if not client.rag_available():
            await interaction.followup.send("RAG module is not available.")
            return
        success = await client.rag_reset()
        if success:
            await interaction.followup.send("Knowledge base cleared.")
        else:
            await interaction.followup.send("Failed to clear knowledge base.")

    # ── Meetings ──────────────────────────────────────────────────────────────

    if VOICE_AVAILABLE:
        meeting_group = app_commands.Group(name="meeting", description="Meeting recording commands")

        @meeting_group.command(name="start", description="Join voice channel and start recording a meeting")
        @app_commands.describe(
            title="Meeting title (used in the summary)",
            summary_channel="Channel where the summary will be posted (defaults to current channel)"
        )
        @exec_only()
        async def meeting_start(
            self,
            interaction: discord.Interaction,
            title: str,
            summary_channel: Optional[discord.TextChannel] = None,
        ):
            await interaction.response.defer(thinking=True)
            channel = summary_channel or interaction.channel
            msg = await start_meeting(interaction, title, channel)
            await interaction.followup.send(msg)

        @meeting_group.command(name="end", description="Stop recording and generate meeting summary")
        @exec_only()
        async def meeting_end(self, interaction: discord.Interaction):
            await interaction.response.defer(thinking=True)
            msg = await end_meeting(interaction)
            await interaction.followup.send(msg)
