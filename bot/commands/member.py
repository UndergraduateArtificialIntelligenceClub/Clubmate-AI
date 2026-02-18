"""
Member-facing slash commands for Clubmate AI.
Available to all Discord server members.
"""

import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)

CHAT_TIMEOUT = 120  # seconds — give enough time for RAG + Gemini + MCP on first run


async def _wait_for_prewarm(bot):
    """Wait for the bot's pre-warm task to finish before handling commands."""
    task = getattr(bot, '_prewarm_task', None)
    if task and not task.done():
        await task


async def _chat_with_timeout(client, prompt: str) -> str:
    """Run client.chat() with a timeout, returning a friendly error on timeout."""
    try:
        return await asyncio.wait_for(client.chat(prompt), timeout=CHAT_TIMEOUT)
    except asyncio.TimeoutError:
        return "⏱️ The request timed out. The bot may be busy — please try again in a moment."
    except Exception as e:
        logger.error("Chat error: %s", e)
        return f"❌ Something went wrong: {e}"


def _split(text: str, limit: int = 1900) -> list[str]:
    return [text[i : i + limit] for i in range(0, len(text), limit)]


class MemberCog(commands.Cog):
    def __init__(self, bot: commands.Bot, session_manager):
        self.bot = bot
        self.sessions = session_manager

    @app_commands.command(name="ask", description="Ask Clubmate a question")
    @app_commands.describe(question="Your question")
    async def ask(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer(thinking=True)
        await _wait_for_prewarm(self.bot)
        client = await self.sessions.get(interaction.channel_id)
        response = await _chat_with_timeout(client, question)
        first, *rest = _split(response)
        await interaction.followup.send(first)
        for chunk in rest:
            await interaction.followup.send(chunk)

    @app_commands.command(name="events", description="List upcoming club events from Google Calendar")
    async def events(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        await _wait_for_prewarm(self.bot)
        client = await self.sessions.get(interaction.channel_id)
        response = await _chat_with_timeout(client, "List the next 10 upcoming events on our club calendar.")
        await interaction.followup.send(response)

    @app_commands.command(name="rooms", description="Check UAlberta library study room availability")
    @app_commands.describe(
        library="Library name: cameron or sperber",
        date="Date to check (YYYY-MM-DD, defaults to today)"
    )
    async def rooms(
        self,
        interaction: discord.Interaction,
        library: str = "cameron",
        date: str = "",
    ):
        await interaction.response.defer(thinking=True)
        # Call libcal directly — no need to go through Gemini for a simple availability lookup
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
            from mcp_servers.libcal import fetch_availability, parse_slots, format_results
            from datetime import datetime

            location_key = library.lower().strip()
            date_str = date or datetime.now().strftime("%Y-%m-%d")

            def _fetch():
                data = fetch_availability(location_key, date_str)
                if not data:
                    return f"❌ Could not fetch availability for {location_key}."
                categorized = parse_slots(data, location_key)
                available = categorized.get("Available", [])
                by_room = {}
                for slot in available:
                    room = slot["room"]
                    if room not in by_room:
                        by_room[room] = []
                    by_room[room].append(f"{slot['start']}-{slot['end']}")
                results = {
                    "library": location_key.capitalize() + " Library",
                    "location": location_key,
                    "date": date_str,
                    "time_filter": None,
                    "available_by_room": by_room,
                    "total_available_slots": len(available),
                }
                return format_results(results) + "\n\nBook at: https://libcal.ualberta.ca/"

            result = await asyncio.to_thread(_fetch)
            for chunk in _split(result):
                await interaction.followup.send(chunk)
        except Exception as e:
            logger.error("LibCal direct call failed: %s", e)
            await interaction.followup.send(f"❌ Could not fetch room availability: {e}")

    @app_commands.command(name="clear", description="Clear conversation history with the bot")
    async def clear(self, interaction: discord.Interaction):
        client = await self.sessions.get(interaction.channel_id)
        client.clear_history()
        await interaction.response.send_message("Conversation history cleared.", ephemeral=True)

    @app_commands.command(name="help", description="Show available commands")
    async def help_cmd(self, interaction: discord.Interaction):
        from bot.permissions import is_exec
        embed = discord.Embed(title="Clubmate AI — Commands", color=0x5865F2)

        embed.add_field(
            name="Member Commands",
            value=(
                "`/ask` — Ask a question\n"
                "`/events` — Upcoming club events\n"
                "`/rooms` — Library room availability\n"
                "`/clear` — Clear chat history\n"
                "`/help` — This message"
            ),
            inline=False,
        )

        if is_exec(interaction):
            embed.add_field(
                name="Exec Commands",
                value=(
                    "`/schedule` — Schedule a meeting\n"
                    "`/cancel-meeting` — Cancel a meeting\n"
                    "`/reschedule` — Reschedule a meeting\n"
                    "`/invite` — Add attendees to a meeting\n"
                    "`/create-doc` — Create a Google Doc\n"
                    "`/create-form` — Create a Google Form\n"
                    "`/form-responses` — View form responses\n"
                    "`/read-sheet` — Read a Google Sheet\n"
                    "`/ingest` — Add to knowledge base\n"
                    "`/kb-reset` — Clear knowledge base\n"
                    "`/meeting start` — Start recording a meeting\n"
                    "`/meeting end` — End recording and get summary"
                ),
                inline=False,
            )

        embed.set_footer(text="Tip: You can also @mention me to ask anything!")
        await interaction.response.send_message(embed=embed, ephemeral=True)
