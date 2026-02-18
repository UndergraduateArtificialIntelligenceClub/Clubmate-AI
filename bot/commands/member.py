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
CALENDAR_TIMEOUT = 60


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
        err_text = str(e)
        if "API key was reported as leaked" in err_text or "PERMISSION_DENIED" in err_text:
            return (
                "❌ Gemini API key is invalid/revoked.\n"
                "Update `GEMINI_API_KEY` in Dashboard → Settings → API Keys, "
                "then restart the bot."
            )
        return f"❌ Something went wrong: {e}"


def _split(text: str, limit: int = 1900) -> list[str]:
    return [text[i : i + limit] for i in range(0, len(text), limit)]


def _format_day_events(result: dict) -> str:
    if "error" in result:
        return f"❌ {result['error']}"
    events = result.get("events") or []
    if not events:
        return result.get("message", "No events found for that day.")

    lines = [f"**Schedule for {result.get('date')}** ({result.get('timezone')})"]
    for event in events:
        start = event.get("start", "Unknown start")
        end = event.get("end", "Unknown end")
        title = event.get("summary", "No Title")
        attendees = event.get("attendees") or []
        attendee_count = f" | 👥 {len(attendees)} attendee(s)" if attendees else ""
        lines.append(f"- `{start} → {end}` — **{title}**{attendee_count}")
    return "\n".join(lines)


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

    @app_commands.command(name="events", description="List upcoming events or events on a specific date")
    @app_commands.describe(date="Optional date in YYYY-MM-DD format")
    async def events(self, interaction: discord.Interaction, date: str = ""):
        await interaction.response.defer(thinking=True)
        await _wait_for_prewarm(self.bot)
        try:
            if date.strip():
                from mcp_servers.google_calendar import list_events_on_date

                result = await asyncio.wait_for(
                    asyncio.to_thread(list_events_on_date, date.strip()),
                    timeout=CALENDAR_TIMEOUT,
                )
                response = _format_day_events(result)
            else:
                from mcp_servers.google_calendar import list_upcoming_events

                response = await asyncio.wait_for(
                    asyncio.to_thread(list_upcoming_events, 10),
                    timeout=CALENDAR_TIMEOUT,
                )

            for chunk in _split(response):
                await interaction.followup.send(chunk)
        except asyncio.TimeoutError:
            await interaction.followup.send("⏱️ Calendar lookup timed out. Please try again.")
        except Exception as e:
            logger.error("Events lookup failed: %s", e)
            await interaction.followup.send(f"❌ Could not fetch events: {e}")

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
                "`/events` — Upcoming events (or pass a date)\n"
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
                    "`/day-schedule` — Show meetings on a specific date\n"
                    "`/cancel-day` — Cancel a meeting by date + name\n"
                    "`/reschedule-day` — Reschedule by date + name\n"
                    "`/invite-day` — Invite attendees by date + name\n"
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
