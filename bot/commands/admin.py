"""
Exec-only slash commands for Clubmate AI.
Requires the configured exec role (set in dashboard → Permissions).
"""

import logging
from pathlib import Path
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from bot.permissions import exec_only
from config import settings

logger = logging.getLogger(__name__)


async def _wait_for_prewarm(bot):
    """Wait for the bot's pre-warm task before handling commands."""
    task = getattr(bot, '_prewarm_task', None)
    if task and not task.done():
        await task

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
        response = await client.chat(f"Schedule a meeting: {details}")
        await interaction.followup.send(response)

    @app_commands.command(name="cancel-meeting", description="Cancel a meeting on Google Calendar")
    @app_commands.describe(details="Meeting name and date to cancel")
    @exec_only()
    async def cancel_meeting(self, interaction: discord.Interaction, details: str):
        await interaction.response.defer(thinking=True)
        await _wait_for_prewarm(self.bot)
        client = await self.sessions.get(interaction.channel_id)
        response = await client.chat(f"Cancel this meeting: {details}")
        await interaction.followup.send(response)

    @app_commands.command(name="reschedule", description="Reschedule a meeting")
    @app_commands.describe(details="Meeting name, current date, and new time")
    @exec_only()
    async def reschedule(self, interaction: discord.Interaction, details: str):
        await interaction.response.defer(thinking=True)
        await _wait_for_prewarm(self.bot)
        client = await self.sessions.get(interaction.channel_id)
        response = await client.chat(f"Reschedule this meeting: {details}")
        await interaction.followup.send(response)

    @app_commands.command(name="invite", description="Add members to an existing meeting")
    @app_commands.describe(details="Meeting name/date and email addresses to add")
    @exec_only()
    async def invite(self, interaction: discord.Interaction, details: str):
        await interaction.response.defer(thinking=True)
        await _wait_for_prewarm(self.bot)
        client = await self.sessions.get(interaction.channel_id)
        response = await client.chat(f"Add these people to the meeting: {details}")
        await interaction.followup.send(response)

    # ── Docs / Sheets / Forms ─────────────────────────────────────────────────

    @app_commands.command(name="create-doc", description="Create a new Google Document")
    @app_commands.describe(details="Document title and optional initial content")
    @exec_only()
    async def create_doc(self, interaction: discord.Interaction, details: str):
        await interaction.response.defer(thinking=True)
        await _wait_for_prewarm(self.bot)
        client = await self.sessions.get(interaction.channel_id)
        response = await client.chat(f"Create a Google Doc: {details}")
        await interaction.followup.send(response)

    @app_commands.command(name="create-form", description="Create a Google Form")
    @app_commands.describe(details="Describe the form — title, purpose, and questions to include")
    @exec_only()
    async def create_form(self, interaction: discord.Interaction, details: str):
        await interaction.response.defer(thinking=True)
        await _wait_for_prewarm(self.bot)
        client = await self.sessions.get(interaction.channel_id)
        response = await client.chat(f"Create a Google Form: {details}")
        await interaction.followup.send(response)

    @app_commands.command(name="form-responses", description="Get responses from a Google Form")
    @app_commands.describe(form_url="Google Form URL or ID")
    @exec_only()
    async def form_responses(self, interaction: discord.Interaction, form_url: str):
        await interaction.response.defer(thinking=True)
        await _wait_for_prewarm(self.bot)
        client = await self.sessions.get(interaction.channel_id)
        response = await client.chat(f"Get responses from this form: {form_url}")
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
        response = await client.chat(
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

