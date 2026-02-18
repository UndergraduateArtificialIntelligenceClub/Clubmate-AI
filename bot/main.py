"""
Clubmate AI — Discord bot entry point.
Run with: python -m bot.main  (from project root)
"""

import asyncio
import logging
import sys
from pathlib import Path

import discord
from discord.ext import commands

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import settings
from bot.client import GeminiMCPClient
from bot.commands.admin import AdminCog
from bot.commands.member import MemberCog

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
# Suppress noisy libraries
for lib in ["discord", "httpx", "httpcore", "chromadb", "sentence_transformers"]:
    logging.getLogger(lib).setLevel(logging.WARNING)

logger = logging.getLogger("clubmate.bot")


class SessionManager:
    """
    Maintains one GeminiMCPClient per Discord channel.
    Each channel gets isolated conversation history.
    """

    def __init__(self):
        self._sessions: dict[int, GeminiMCPClient] = {}

    async def get(self, channel_id: int) -> GeminiMCPClient:
        if channel_id not in self._sessions:
            logger.info("Creating new session for channel %d", channel_id)
            client = GeminiMCPClient()
            await client.connect_all()
            self._sessions[channel_id] = client
        return self._sessions[channel_id]

    async def close_all(self):
        for client in self._sessions.values():
            await client.close()
        self._sessions.clear()


class ClubmateBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        self.session_manager = SessionManager()

    async def setup_hook(self):
        # Register cogs
        await self.add_cog(AdminCog(self, self.session_manager))
        await self.add_cog(MemberCog(self, self.session_manager))

        # Sync slash commands to the configured guild
        if settings.discord_guild_id:
            guild = discord.Object(id=int(settings.discord_guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info("Slash commands synced to guild %s", settings.discord_guild_id)
        else:
            await self.tree.sync()
            logger.info("Slash commands synced globally")

    async def on_ready(self):
        logger.info("Clubmate AI online as %s (ID: %s)", self.user, self.user.id)
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening, name="/ask | /help"
            )
        )
        # Pre-warm MCP connections and RAG so first command doesn't time out
        # Store the task so commands can await it before proceeding
        self._prewarm_task = asyncio.create_task(self._prewarm())

    async def on_app_command_error(
        self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError
    ):
        if isinstance(error, discord.app_commands.CheckFailure):
            await interaction.response.send_message(str(error), ephemeral=True)
        else:
            logger.error("Command error: %s", error)
            msg = "Something went wrong. Please try again."
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        await self.process_commands(message)

        # Respond to @mentions as a natural chat
        if self.user.mentioned_in(message) and not message.content.startswith("!"):
            prompt = message.content.replace(f"<@{self.user.id}>", "").strip()
            if not prompt:
                return
            async with message.channel.typing():
                try:
                    client = await self.session_manager.get(message.channel.id)
                    response = await client.chat(prompt)
                    chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                    for chunk in chunks:
                        await message.reply(chunk)
                except Exception as e:
                    logger.error("Chat error on mention: %s", e)
                    await message.reply("Something went wrong. Please try again.")

    async def _prewarm(self):
        """Pre-warm MCP connections and RAG index so the first command is fast."""
        try:
            logger.info("Pre-warming MCP sessions and RAG...")
            # Use channel_id=0 as the "default" warm session
            await self.session_manager.get(0)
            logger.info("Pre-warm complete.")
        except Exception as e:
            logger.warning("Pre-warm failed (non-fatal): %s", e)

    async def close(self):
        await self.session_manager.close_all()
        await super().close()


def main():
    if not settings.discord_token:
        logger.error("DISCORD_TOKEN is not set in .env")
        sys.exit(1)

    bot = ClubmateBot()
    bot.run(settings.discord_token, log_handler=None)


if __name__ == "__main__":
    main()
