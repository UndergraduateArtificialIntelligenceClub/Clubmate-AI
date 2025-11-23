"""
CLI interface for the Gemini MCP Client
Provides an interactive shell for chatting with Gemini via MCP servers
"""

import asyncio
import sys
from typing import Optional
from pathlib import Path

from gemini_mcp_client import GeminiMCPClient

import click


class CLIClient:
    """Interactive CLI client for Gemini MCP"""

    def __init__(self):
        self.client: Optional[GeminiMCPClient] = None
        self.running = True

    async def initialize(self):
        """Initialize the client"""
        try:
            self.client = GeminiMCPClient()
            print("✓ Gemini MCP Client initialized")
        except ValueError as e:
            print(f"✗ Error: {e}")
            print("Please set GEMINI_API_KEY environment variable")
            sys.exit(1)

    async def cmd_help(self, args: list):
        """Show help information"""
        help_text = """
Available Commands:
  servers add <name> <path> [language] [description]  - Add a new server
  servers list                                         - List all servers
  servers remove <name>                                - Remove a server
  servers info <name>                                  - Show server info
  
  connect <server_name>                                - Connect to a server
  disconnect [server_name]                             - Disconnect from server(s)
  status                                               - Show connection status
  
  tools [server_name]                                  - List available tools
  
  chat                                                 - Enter chat mode
  history                                              - Show conversation history
  clear-history                                        - Clear conversation history
  
  model <model_name>                                   - Set default model
  models                                               - List available models
  
  exit, quit                                           - Exit the program
  help                                                 - Show this help
        """
        print(help_text)

    async def cmd_servers_add(self, args: list):
        """Add a new server"""
        if len(args) < 2:
            print("Usage: servers add <name> <path> [language] [description]")
            return

        name = args[0]
        path = args[1]
        language = args[2] if len(args) > 2 else "python"
        description = " ".join(args[3:]) if len(args) > 3 else ""

        try:
            self.client.add_server(name, path, language, description=description)
            print(f"✓ Added server '{name}'")
        except Exception as e:
            print(f"✗ Error: {e}")

    async def cmd_servers_list(self, args: list):
        """List all servers"""
        servers = self.client.list_servers()
        if not servers:
            print("No servers configured")
            return

        print("\nConfigured Servers:")
        for name in servers:
            config = self.client.servers[name]
            status = "●" if name == self.client.active_server else "○"
            print(f"  {status} {name}: {config.script_path} ({config.language})")
            if config.description:
                print(f"      {config.description}")

    async def cmd_servers_remove(self, args: list):
        """Remove a server"""
        if not args:
            print("Usage: servers remove <name>")
            return

        name = args[0]
        self.client.remove_server(name)
        print(f"✓ Removed server '{name}'")

    async def cmd_servers_info(self, args: list):
        """Show server info"""
        if not args:
            print("Usage: servers info <name>")
            return

        name = args[0]
        if name not in self.client.servers:
            print(f"✗ Server '{name}' not found")
            return

        config = self.client.servers[name]
        print(f"\nServer: {name}")
        print(f"  Path: {config.script_path}")
        print(f"  Language: {config.language}")
        if config.description:
            print(f"  Description: {config.description}")
        if config.env_vars:
            print(f"  Environment: {config.env_vars}")

    async def cmd_connect(self, args: list):
        """Connect to a server"""
        if not args:
            print("Usage: connect <server_name>")
            return

        name = args[0]
        try:
            await self.client.connect(name)
            print(f"✓ Connected to '{name}'")
        except Exception as e:
            print(f"✗ Error: {e}")

    async def cmd_disconnect(self, args: list):
        """Disconnect from server(s)"""
        server_name = args[0] if args else None
        await self.client.disconnect(server_name)
        if server_name:
            print(f"✓ Disconnected from '{server_name}'")
        else:
            print("✓ Disconnected from all servers")

    async def cmd_status(self, args: list):
        """Show connection status"""
        if not self.client.active_server:
            print("Not connected to any server")
            return

        print(f"Connected to: {self.client.active_server}")
        try:
            tools = await self.client.get_tools()
            print(f"Available tools: {len(tools)}")
            for tool_name in list(tools.keys())[:5]:
                print(f"  - {tool_name}")
            if len(tools) > 5:
                print(f"  ... and {len(tools) - 5} more")
        except Exception as e:
            print(f"Error getting tools: {e}")

    async def cmd_tools(self, args: list):
        """List available tools"""
        if not self.client.active_server:
            print("Not connected to any server")
            return

        try:
            tools = await self.client.get_tools()
            print(f"\nAvailable Tools ({len(tools)} total):")
            for tool_name, tool in tools.items():
                print(f"  - {tool_name}")
                if hasattr(tool, "description") and tool.description:
                    print(f"      {tool.description}")
        except Exception as e:
            print(f"✗ Error: {e}")

    async def cmd_chat(self, args: list):
        """Enter interactive chat mode"""
        if not self.client.active_server:
            print("✗ Not connected to any server")
            print("Use 'connect <server_name>' first")
            return

        print(f"\nChat mode (connected to {self.client.active_server})")
        print("Type 'exit' or 'quit' to return to main menu, 'help' for commands\n")

        while True:
            try:
                user_input = input("You: ").strip()
            except EOFError:
                break

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit"]:
                break

            if user_input.lower() == "clear":
                self.client.clear_history()
                print("Conversation history cleared")
                continue

            try:
                print("Thinking...", end="", flush=True)
                response = await self.client.chat(user_input)
                print(f"\rGemini: {response}\n")
            except Exception as e:
                print(f"\r✗ Error: {e}\n")

    async def cmd_history(self, args: list):
        """Show conversation history"""
        history = self.client.get_conversation_history()
        if not history:
            print("No conversation history")
            return

        print("\nConversation History:")
        for i, msg in enumerate(history, 1):
            role = msg["role"].upper()
            content = (
                msg["content"][:100] + "..."
                if len(msg["content"]) > 100
                else msg["content"]
            )
            print(f"{i}. [{role}] {content}")

    async def cmd_clear_history(self, args: list):
        """Clear conversation history"""
        self.client.clear_history()
        print("✓ Conversation history cleared")

    async def cmd_models(self, args: list):
        """List available Gemini models"""
        models = [
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]
        print("\nAvailable Models:")
        for model in models:
            print(f"  - {model}")

    async def process_command(self, line: str):
        """Process a command line"""
        if not line.strip():
            return

        parts = line.strip().split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        # Command routing
        if command == "help":
            await self.cmd_help(args)
        elif command == "servers":
            if args and args[0] == "add":
                await self.cmd_servers_add(args[1:])
            elif args and args[0] == "list":
                await self.cmd_servers_list(args[1:])
            elif args and args[0] == "remove":
                await self.cmd_servers_remove(args[1:])
            elif args and args[0] == "info":
                await self.cmd_servers_info(args[1:])
            else:
                await self.cmd_servers_list([])
        elif command == "connect":
            await self.cmd_connect(args)
        elif command == "disconnect":
            await self.cmd_disconnect(args)
        elif command == "status":
            await self.cmd_status(args)
        elif command == "tools":
            await self.cmd_tools(args)
        elif command == "chat":
            await self.cmd_chat(args)
        elif command == "history":
            await self.cmd_history(args)
        elif command == "clear-history":
            await self.cmd_clear_history(args)
        elif command == "models":
            await self.cmd_models(args)
        elif command in ["exit", "quit"]:
            self.running = False
        else:
            print(f"Unknown command: {command}. Type 'help' for available commands.")

    async def run(self):
        """Run the interactive CLI"""
        await self.initialize()

        print(
            """
╔══════════════════════════════════════╗
║   Gemini MCP Client v1.0             ║
║   Type 'help' for available commands ║
╚══════════════════════════════════════╝
        """
        )

        try:
            while self.running:
                try:
                    user_input = input("gemini-mcp> ").strip()
                    if user_input:
                        await self.process_command(user_input)
                except KeyboardInterrupt:
                    print("\nUse 'exit' or 'quit' to exit")
                except EOFError:
                    break
        finally:
            await self.client.close()
            print("Goodbye!")


@click.group()
def cli():
    """Gemini MCP Client - Interactive CLI"""
    pass


@cli.command()
def interactive():
    """Run the interactive CLI"""
    cli_client = CLIClient()
    asyncio.run(cli_client.run())


if __name__ == "__main__":
    cli_client = CLIClient()
    asyncio.run(cli_client.run())
