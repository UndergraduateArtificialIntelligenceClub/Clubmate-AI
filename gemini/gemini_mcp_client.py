"""
Gemini MCP Client - A comprehensive client for integrating Gemini with MCP servers
"""

import asyncio
import json
import logging
import os
import sys
from contextlib import AsyncExitStack
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- RAG Integration Setup ---
# Load .env at module level so GEMINI_API_KEY is available before ragbot import
load_dotenv()

# Add project root to sys.path so ragbot package can be imported
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

try:
    from ragbot import rag_retrieve, rag_has_documents, rag_ingest, db_reset as rag_db_reset
    RAG_AVAILABLE = True
    logger.info("RAG module loaded successfully")
except ImportError:
    RAG_AVAILABLE = False
    logger.info("ragbot module not available; RAG features disabled")
except ValueError as e:
    RAG_AVAILABLE = False
    logger.warning(f"ragbot configuration error: {e}; RAG features disabled")


@dataclass
class ServerConfig:
    """Configuration for an MCP server"""

    name: str
    script_path: str
    language: str  # 'python' or 'node'
    env_vars: Optional[Dict[str, str]] = None
    description: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class ConversationMessage:
    """A message in the conversation history"""

    role: str  # 'user' or 'model'
    content: str


class GeminiMCPClient:
    """
    A comprehensive Gemini MCP client with support for:
    - Multiple MCP servers
    - Conversation memory
    - Tool discovery and execution
    - Server configuration management
    - Multiple Gemini models
    """

    def __init__(
        self, api_key: Optional[str] = None, config_file: str = "mcp_servers.json"
    ):
        """
        Initialize the Gemini MCP client

        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            config_file: Path to server configuration file
        """
        load_dotenv()

        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment or arguments")

        self.gemini_client = genai.Client(api_key=self.api_key)

        # Server management
        self.config_file = config_file
        self.servers: Dict[str, ServerConfig] = {}
        self.sessions: Dict[str, ClientSession] = {}
        self.active_server: Optional[str] = None

        # Conversation memory
        self.conversation_history: List[ConversationMessage] = []

        # Connection management
        self.exit_stack = AsyncExitStack()

        # Load existing configurations
        self._load_server_configs()

        logger.info("Gemini MCP Client initialized")

    def _load_server_configs(self):
        """Load server configurations from file"""
        if Path(self.config_file).exists():
            try:
                with open(self.config_file, "r") as f:
                    configs = json.load(f)
                    for name, config in configs.items():
                        self.servers[name] = ServerConfig(**config)
                logger.info(f"Loaded {len(self.servers)} server configurations")
            except Exception as e:
                logger.warning(f"Failed to load server configs: {e}")

    def _save_server_configs(self):
        """Save server configurations to file"""
        try:
            configs = {name: server.to_dict() for name, server in self.servers.items()}
            with open(self.config_file, "w") as f:
                json.dump(configs, f, indent=2)
            logger.info("Server configurations saved")
        except Exception as e:
            logger.error(f"Failed to save server configs: {e}")

    def add_server(
        self,
        name: str,
        script_path: str,
        language: str = "python",
        env_vars: Optional[Dict[str, str]] = None,
        description: str = "",
    ):
        """
        Add a new MCP server configuration
        """
        if not Path(script_path).exists():
            raise FileNotFoundError(f"Server script not found: {script_path}")

        if language not in ["python", "node"]:
            raise ValueError("Language must be 'python' or 'node'")

        self.servers[name] = ServerConfig(
            name=name,
            script_path=script_path,
            language=language,
            env_vars=env_vars,
            description=description,
        )
        self._save_server_configs()
        logger.info(f"Added server configuration: {name}")

    def remove_server(self, name: str):
        """Remove a server configuration"""
        if name in self.servers:
            del self.servers[name]
            if self.active_server == name:
                self.active_server = None
            self._save_server_configs()
            logger.info(f"Removed server configuration: {name}")

    def list_servers(self) -> List[str]:
        """List all configured servers"""
        return list(self.servers.keys())

    async def connect(self, server_name: str) -> ClientSession:
        """
        Connect to an MCP server
        """
        if server_name not in self.servers:
            raise ValueError(f"Server '{server_name}' not configured")

        if server_name in self.sessions:
            logger.info(f"Already connected to {server_name}")
            self.active_server = server_name
            return self.sessions[server_name]

        config = self.servers[server_name]
        cmd = "python" if config.language == "python" else "node"

        try:
            params = StdioServerParameters(
                command=cmd, args=[config.script_path], env=config.env_vars
            )

            # stdio_client yields (read, write) streams
            read, write = await self.exit_stack.enter_async_context(
                stdio_client(params)
            )

            # Create ClientSession with the streams
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )

            # Initialize the session
            await session.initialize()

            self.sessions[server_name] = session
            self.active_server = server_name
            logger.info(f"Connected to MCP server: {server_name}")
            return session

        except Exception as e:
            logger.error(f"Failed to connect to {server_name}: {e}")
            raise

    async def disconnect(self, server_name: Optional[str] = None):
        """Disconnect from an MCP server"""
        if server_name:
            if server_name in self.sessions:
                del self.sessions[server_name]
                if self.active_server == server_name:
                    self.active_server = None
                logger.info(f"Disconnected from {server_name}")
        else:
            self.sessions.clear()
            self.active_server = None
            logger.info("Disconnected from all servers")

    async def get_tools(self, server_name: Optional[str] = None) -> Dict[str, Any]:
        """Get available tools from an MCP server"""
        server = server_name or self.active_server
        if not server or server not in self.sessions:
            raise ValueError("No active server or server not connected")

        session = self.sessions[server]
        try:
            tools_response = await session.list_tools()
            tools = {tool.name: tool for tool in tools_response.tools}
            logger.info(f"Retrieved {len(tools)} tools from {server}")
            return tools
        except Exception as e:
            logger.error(f"Failed to get tools: {e}")
            raise

    async def chat(
        self,
        prompt: str,
        model: str = "gemini-2.0-flash",
        server_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """
        Send a chat message to Gemini with MCP tools available and recursive execution
        """
        server = server_name or self.active_server
        if not server or server not in self.sessions:
            raise ValueError("No active server or server not connected")

        # Add user message to history
        self.conversation_history.append(ConversationMessage("user", prompt))

        try:
            session = self.sessions[server]

            # Get available tools from MCP server
            tools_response = await session.list_tools()
            tools = tools_response.tools if tools_response.tools else []

            # 1. Build initial message list from history
            messages = []
            for msg in self.conversation_history:
                messages.append({"role": msg.role, "parts": [{"text": msg.content}]})

            # 2. Build comprehensive system prompt
            system_prompt = f"""You are Clubmate, an intelligent AI assistant with two capabilities:

## Knowledge Base (RAG)
If knowledge base context is provided below, it contains pre-retrieved information relevant to the user's question. Use this for:
- FAQ-style questions about ingested documents
- Static information from PDFs, text files, or documentation
- Questions about policies, procedures, or reference material

When using knowledge base context:
- Answer directly from the provided context - DO NOT call any tools to "search" documents
- If the context doesn't contain the answer, say so clearly

## MCP Tools
You have access to tools from the connected MCP server '{server}'. Only call tools that are explicitly listed in your tool context. Do NOT invent tool names.

## Response Guidelines
1. For knowledge-based questions → Use the provided context directly
2. For calendar/action questions → Use MCP tools
3. For mixed questions → Combine both approaches
4. Be concise but comprehensive
5. Maintain a friendly, professional tone
"""

            # 2b. Inject RAG context if available
            rag_context = await self._retrieve_rag_context(prompt)
            if rag_context:
                system_prompt += f"""
---
## Knowledge Base Context
The following information was retrieved from the ingested knowledge base and is directly available to you:

{rag_context}

NOTE: This context is already provided - you do NOT need to call any tools to access it.
---
"""

            # 3. Initial API Call
            response = await self.gemini_client.aio.models.generate_content(
                model=model,
                contents=messages,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    tools=[session] if tools else None,
                    system_instruction=system_prompt,
                ),
            )

            # 4. Handle Tool Loop (Recursion)
            final_text = await self._handle_tool_calls(
                response,
                session,
                messages,
                model,
                system_prompt,
                temperature,
                max_tokens,
            )

            # Add final model response to history
            self.conversation_history.append(
                ConversationMessage("model", final_text)
            )

            logger.info(f"Chat completed with {server}")
            return final_text

        except Exception as e:
            logger.error(f"Chat failed: {e}")
            raise

    async def _handle_tool_calls(
        self,
        response: Any,
        session: ClientSession,
        messages: List[Dict],
        model: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """
        Handle tool calls from Gemini response in a loop until a text response is generated.
        """

        while True:
            # Check if there are function calls in the response
            # Note: Google GenAI SDK structure varies slightly by version, checking attributes safely
            function_calls = []
            if hasattr(response, "function_calls") and response.function_calls:
                function_calls = response.function_calls
            elif hasattr(response, "candidates") and response.candidates:
                part = response.candidates[0].content.parts[0]
                if hasattr(part, "function_call") and part.function_call:
                    # If the first part is a function call, we might have multiple
                    function_calls = [
                        p.function_call
                        for p in response.candidates[0].content.parts
                        if p.function_call
                    ]

            # If no tools called, return the text
            if not function_calls:
                if hasattr(response, "text") and response.text:
                    return response.text
                return "Task completed (No text output)."

            logger.info(f"Gemini requested {len(function_calls)} tool calls")

            # Append the model's request (Function Call) to the message history
            # This is crucial so the model remembers it asked for a tool
            messages.append(response.candidates[0].content)

            # Execute tools
            parts = []
            for call in function_calls:
                try:
                    logger.info(f"Executing tool: {call.name} with args: {call.args}")

                    # Execute via MCP Session
                    result = await session.call_tool(call.name, arguments=call.args)

                    # Extract text content from result
                    # MCP returns a list of content items (TextContent or ImageContent)
                    content_str = ""
                    if hasattr(result, "content") and result.content:
                        for item in result.content:
                            if hasattr(item, "text"):
                                content_str += item.text
                    else:
                        content_str = str(result)

                    # Create response part
                    parts.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=call.name, response={"result": content_str}
                            )
                        )
                    )

                except Exception as e:
                    logger.error(f"Error executing tool {call.name}: {e}")
                    parts.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=call.name, response={"error": str(e)}
                            )
                        )
                    )

            # Append tool results to history
            messages.append({"role": "user", "parts": parts})

            # Send back to Gemini to get the next step (or final answer)
            response = await self.gemini_client.aio.models.generate_content(
                model=model,
                contents=messages,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    tools=[session],  # Keep tools available for multi-step workflows
                    system_instruction=system_prompt,
                ),
            )

            # Loop continues...

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the conversation history"""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.conversation_history
        ]

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()
        logger.info("Conversation history cleared")

    async def _retrieve_rag_context(self, query: str, top_k: int = 5) -> Optional[str]:
        """
        Retrieve relevant RAG context for the given query.

        Returns a formatted context string, or None if RAG is unavailable
        or the vector store has no documents.
        """
        if not RAG_AVAILABLE:
            return None

        try:
            has_docs = await asyncio.to_thread(rag_has_documents)
            if not has_docs:
                logger.debug("RAG vector store is empty; skipping context retrieval")
                return None

            chunks = await asyncio.to_thread(rag_retrieve, query, top_k)

            if not chunks:
                return None

            context_parts = []
            for i, chunk in enumerate(chunks, 1):
                source = chunk["source"]
                page = chunk.get("page")
                citation = f"[{source}, page {page}]" if page else f"[{source}]"
                context_parts.append(f"Reference {i} {citation}:\n{chunk['content']}")

            return "\n---\n".join(context_parts)

        except Exception as e:
            logger.warning(f"RAG context retrieval failed: {e}")
            return None

    @staticmethod
    async def ingest_documents(path: str) -> bool:
        """Ingest documents into the RAG knowledge base."""
        if not RAG_AVAILABLE:
            raise RuntimeError("RAG module is not available")
        return await asyncio.to_thread(rag_ingest, path)

    @staticmethod
    async def reset_rag_db() -> bool:
        """Reset the RAG vector database."""
        if not RAG_AVAILABLE:
            raise RuntimeError("RAG module is not available")
        return await asyncio.to_thread(rag_db_reset)

    @staticmethod
    def is_rag_available() -> bool:
        """Check if RAG functionality is available."""
        return RAG_AVAILABLE

    async def close(self):
        """Close all connections"""
        await self.exit_stack.aclose()
        self.sessions.clear()
        logger.info("Client closed")


async def main_example():
    """Example usage of the Gemini MCP client"""

    # Initialize client
    client = GeminiMCPClient()

    # Add a server configuration (example with a simple echo server)
    try:
        client.add_server(
            name="example-server",
            script_path="./example_server.py",
            language="python",
            description="Example MCP server",
        )
    except FileNotFoundError:
        print(
            "Note: Example server not found. You can add your own with client.add_server()"
        )
        return

    try:
        # Connect to server
        await client.connect("example-server")

        # Chat with Gemini
        print("\nSending prompt: 'Roll 5 dice and then tell me the sum.'")
        response = await client.chat(
            "Roll 5 dice and then tell me the sum.", model="gemini-2.0-flash"
        )
        print(f"\nGemini Final Answer: {response}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main_example())
