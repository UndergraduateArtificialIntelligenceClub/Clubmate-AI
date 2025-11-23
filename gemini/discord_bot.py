import os
import asyncio
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Import your existing client
from gemini_mcp_client import GeminiMCPClient

# Configuration
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DEFAULT_SERVER = "example"  # The server to connect to automatically

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DiscordBot")

# Intent setup (Message Content is required)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


class MCPSessionManager:
    """
    Manages separate GeminiMCPClient instances for different Discord channels.
    This ensures conversation history doesn't get mixed up between users/channels.
    """

    def __init__(self):
        self.sessions = {}  # Mapping: channel_id -> GeminiMCPClient

    async def get_or_create_session(self, channel_id):
        if channel_id not in self.sessions:
            logger.info(f"Creating new session for channel {channel_id}")
            client = GeminiMCPClient()
            
            # 1. REGISTER EXAMPLE SERVER (Existing)
            try:
                servers = client.list_servers()
                if "example" not in servers:
                    client.add_server(
                        name="example",
                        script_path="./example_server.py",
                        language="python",
                        description="Utilities: Dice, Math, Weather"
                    )
            except Exception:
                pass

            # 2. REGISTER CALENDAR SERVER (New)
            try:
                servers = client.list_servers()
                if "calendar" not in servers:
                    client.add_server(
                        name="calendar",
                        script_path="../src/servers/calendar_integration.py",
                        language="python",
                        description="Google Calendar: Schedule, Check Availability"
                    )
                    logger.info("Registered Calendar Server")
            except Exception as e:
                logger.error(f"Failed to register calendar: {e}")

            # 3. AUTO CONNECT (Optional - choose which one you want active by default)
            # Currently, the client only supports one active connection at a time.
            # Let's default to 'calendar' since that's what you are working on.
            try:
                await client.connect("calendar")
            except Exception as e:
                logger.error(f"Could not auto-connect to calendar: {e}")
                # Fallback to example if calendar fails
                try:
                    await client.connect("example")
                except:
                    pass
                
            self.sessions[channel_id] = client
            
        return self.sessions[channel_id]
    async def close_all(self):
        for client in self.sessions.values():
            await client.close()


session_manager = MCPSessionManager()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")


@bot.event
async def on_shutdown():
    await session_manager.close_all()


def split_message(text, limit=1900):
    """Split long messages into chunks Discord can handle"""
    return [text[i : i + limit] for i in range(0, len(text), limit)]


@bot.command(name="chat")
async def chat_command(ctx, *, prompt: str):
    """Chat with Gemini (Tools enabled)"""
    async with ctx.typing():
        client = await session_manager.get_or_create_session(ctx.channel.id)

        # Check if connected
        if not client.active_server:
            await ctx.send(
                "🔌 Not connected to any MCP server. Use `!connect <server_name>` first.\nAvailable: "
                + ", ".join(client.list_servers())
            )
            return

        try:
            # We pass the prompt to the client.
            # If you want to change temperature, change it in the client.chat() call below manually
            response = await client.chat(prompt, temperature=0.7)

            # Send response (split if too long)
            for chunk in split_message(response):
                await ctx.send(chunk)

        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")


@bot.command(name="tools")
async def list_tools_command(ctx):
    """List available tools on the current server"""
    client = await session_manager.get_or_create_session(ctx.channel.id)

    if not client.active_server:
        await ctx.send("Not connected to a server.")
        return

    try:
        tools = await client.get_tools()
        if not tools:
            await ctx.send("No tools available on this server.")
            return

        embed = discord.Embed(title=f"Tools on {client.active_server}", color=0x00FF00)
        for name, tool in tools.items():
            desc = getattr(tool, "description", "No description")
            embed.add_field(name=name, value=desc[:1024], inline=False)

        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Error fetching tools: {e}")


@bot.command(name="connect")
async def connect_command(ctx, server_name: str):
    """Connect to a specific MCP server"""
    client = await session_manager.get_or_create_session(ctx.channel.id)

    try:
        await client.connect(server_name)
        await ctx.send(f"✅ Connected to **{server_name}**")
    except ValueError:
        await ctx.send(
            f"❌ Server '{server_name}' not configured. Use `!servers` to see list."
        )
    except Exception as e:
        await ctx.send(f"❌ Connection failed: {str(e)}")


@bot.command(name="servers")
async def servers_command(ctx):
    """List configured servers"""
    client = await session_manager.get_or_create_session(ctx.channel.id)
    servers = client.list_servers()

    status_text = ""
    for s in servers:
        active = "🟢" if s == client.active_server else "⚪"
        status_text += f"{active} **{s}**\n"

    embed = discord.Embed(
        title="MCP Servers",
        description=status_text or "No servers configured",
        color=0x3498DB,
    )
    await ctx.send(embed=embed)


@bot.command(name="clear")
async def clear_history_command(ctx):
    """Clear conversation memory"""
    client = await session_manager.get_or_create_session(ctx.channel.id)
    client.clear_history()
    await ctx.send("🧹 Conversation history cleared.")


# Allow chatting by just mentioning the bot
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Process commands first (!chat, !connect, etc)
    await bot.process_commands(message)

    # If the message mentions the bot but isn't a command, treat it as a chat
    if bot.user.mentioned_in(message) and not message.content.startswith("!"):
        # Remove the mention from the prompt to avoid confusing Gemini
        prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if prompt:
            # Reuse the chat logic
            ctx = await bot.get_context(message)
            await chat_command(ctx, prompt=prompt)


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN not found in .env")
    else:
        bot.run(DISCORD_TOKEN)
