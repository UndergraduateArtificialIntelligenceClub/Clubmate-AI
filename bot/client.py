"""
GeminiMCPClient — Gemini AI + MCP tool loop.
Manages connections to MCP servers and drives the Gemini conversation + tool execution cycle.
"""

import asyncio
import logging
import sys
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import settings, PROJECT_ROOT

logger = logging.getLogger(__name__)

# ── RAG integration ───────────────────────────────────────────────────────────
try:
    from ragbot import rag_retrieve, rag_has_documents, rag_ingest, db_reset as rag_db_reset
    RAG_AVAILABLE = True
    logger.info("RAG module loaded")
except Exception as e:
    RAG_AVAILABLE = False
    logger.warning("RAG not available: %s", e)

# ── MCP server registry ───────────────────────────────────────────────────────
# Maps server name → script path relative to project root
MCP_SERVERS: Dict[str, Path] = {
    "calendar": PROJECT_ROOT / "mcp_servers" / "google_calendar.py",
    "docs":     PROJECT_ROOT / "mcp_servers" / "google_docs.py",
    "sheets":   PROJECT_ROOT / "mcp_servers" / "google_sheets.py",
    "forms":    PROJECT_ROOT / "mcp_servers" / "google_forms.py",
    "libcal":   PROJECT_ROOT / "mcp_servers" / "libcal.py",
}

SYSTEM_PROMPT = """You are Clubmate, an AI assistant for a university club Discord server.

## Your Capabilities
1. **Knowledge Base (RAG)** — If context is provided below, use it to answer questions about the club (events, policies, FAQs). Do NOT call tools for this; use the provided context directly.
2. **Google Calendar** — Schedule, cancel, reschedule meetings, manage invites, check availability.
3. **Google Docs** — Read, create, and append to documents.
4. **Google Sheets** — Read and write spreadsheet data.
5. **Google Forms** — Create forms, edit existing forms (add questions / update title-description), and retrieve responses.
6. **LibCal** — Check UAlberta library study room availability.

## Guidelines
- Be concise, friendly, and professional.
- For knowledge-base questions → use the provided context.
- For action requests (calendar, forms, etc.) → use the appropriate MCP tool.
- If a user references an existing Google Form URL/ID and asks to add or edit questions,
  update that existing form rather than creating a new one.
- For Google Form responses, present one respondent at a time with identity first:
  Name if available, otherwise respondent email.
- For large sheet/table outputs, summarize first and avoid dumping full raw rows unless explicitly requested.
- When creating a Google Doc, include substantial initial body content by default
  (not title-only), unless the user explicitly asks for an empty doc.
- For Google Docs content, write plain text suitable for direct doc insertion.
  Do not use Markdown markers like #, *, **, or ``` in the document body.
- Never invent tool names. Only call tools explicitly available to you.
- When you complete an action, confirm it clearly and share any relevant links.
"""


class GeminiMCPClient:
    """
    Manages Gemini AI conversation with MCP tool integration.
    One instance per Discord channel — maintains isolated conversation history.
    """

    def __init__(self):
        self.gemini = genai.Client(api_key=settings.gemini_api_key)
        self.sessions: Dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
        self.history: List[Dict] = []  # Gemini-native message format

    async def connect(self, server_name: str) -> ClientSession:
        """Connect to an MCP server by name. Idempotent — skips if already connected."""
        if server_name in self.sessions:
            return self.sessions[server_name]

        if server_name not in MCP_SERVERS:
            raise ValueError(f"Unknown MCP server: '{server_name}'. Available: {list(MCP_SERVERS)}")

        script = MCP_SERVERS[server_name]
        if not script.exists():
            raise FileNotFoundError(f"MCP server script not found: {script}")

        params = StdioServerParameters(command="python", args=[str(script)])
        read, write = await self.exit_stack.enter_async_context(stdio_client(params))
        session = await self.exit_stack.enter_async_context(ClientSession(read, write))
        await session.initialize()

        self.sessions[server_name] = session
        logger.info("Connected to MCP server: %s", server_name)
        return session

    async def connect_all(self):
        """Connect to all registered MCP servers. Logs but does not raise on individual failures."""
        for name in MCP_SERVERS:
            try:
                await self.connect(name)
            except Exception as e:
                logger.warning("Could not connect to %s: %s", name, e)

    def clear_history(self):
        self.history.clear()

    async def chat(self, prompt: str, include_rag: bool = True) -> str:
        """
        Send a user message. Runs the Gemini + MCP tool loop until a text response is produced.
        RAG context is automatically injected into the system prompt when documents are available.
        """
        # Build system prompt with optional RAG context
        system = SYSTEM_PROMPT
        if include_rag:
            rag_context = await self._rag_context(prompt)
            if rag_context:
                system += f"\n---\n## Knowledge Base Context\n{rag_context}\n---\n"

        # Collect all active sessions as tool sources
        active_sessions = list(self.sessions.values())

        # Append user turn to history
        self.history.append({"role": "user", "parts": [{"text": prompt}]})

        response = await self.gemini.aio.models.generate_content(
            model=settings.default_llm_model,
            contents=self.history,
            config=types.GenerateContentConfig(
                temperature=settings.temperature,
                max_output_tokens=4096,
                tools=active_sessions if active_sessions else None,
                system_instruction=system,
            ),
        )

        final_text = await self._tool_loop(response, active_sessions, system)

        self.history.append({"role": "model", "parts": [{"text": final_text}]})
        return final_text

    async def _tool_loop(
        self,
        response: Any,
        sessions: List[ClientSession],
        system: str,
    ) -> str:
        """Iterate Gemini tool calls until a plain text response is returned."""
        while True:
            function_calls = self._extract_function_calls(response)

            if not function_calls:
                return self._extract_text(response) or "Done."

            logger.info("Tool calls requested: %s", [c.name for c in function_calls])

            # Append model's tool-request turn
            model_content = self._extract_candidate_content(response)
            if model_content is not None:
                self.history.append(model_content)

            # Execute each tool call across all connected sessions
            result_parts = []
            for call in function_calls:
                result_parts.append(await self._execute_tool(call, sessions))

            # Append tool results turn
            self.history.append({"role": "user", "parts": result_parts})

            # Send results back to Gemini
            response = await self.gemini.aio.models.generate_content(
                model=settings.default_llm_model,
                contents=self.history,
                config=types.GenerateContentConfig(
                    temperature=settings.temperature,
                    max_output_tokens=4096,
                    tools=sessions if sessions else None,
                    system_instruction=system,
                ),
            )

    @staticmethod
    def _extract_function_calls(response: Any) -> list:
        if hasattr(response, "function_calls") and response.function_calls:
            return response.function_calls
        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", None) or []
            return [p.function_call for p in parts if getattr(p, "function_call", None)]
        return []

    @staticmethod
    def _extract_candidate_content(response: Any) -> Optional[Any]:
        if hasattr(response, "candidates") and response.candidates:
            return getattr(response.candidates[0], "content", None)
        return None

    @staticmethod
    def _extract_text(response: Any) -> str:
        text = getattr(response, "text", None)
        if text:
            return text
        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", None) or []
            lines = [getattr(p, "text", "") for p in parts if getattr(p, "text", None)]
            return "\n".join(line for line in lines if line).strip()
        return ""

    async def _execute_tool(self, call, sessions: List[ClientSession]) -> types.Part:
        """Try each session until one successfully handles the tool call."""
        last_error = None
        for session in sessions:
            try:
                args = getattr(call, "args", None) or {}
                result = await session.call_tool(call.name, arguments=args)
                content_str = ""
                content = getattr(result, "content", None)
                if content:
                    for item in content:
                        if hasattr(item, "text"):
                            content_str += item.text
                else:
                    content_str = str(result)
                logger.info("Tool %s → success", call.name)
                return types.Part(
                    function_response=types.FunctionResponse(
                        name=call.name, response={"result": content_str}
                    )
                )
            except Exception as e:
                last_error = e
                continue

        logger.error("Tool %s failed on all sessions: %s", call.name, last_error)
        return types.Part(
            function_response=types.FunctionResponse(
                name=call.name, response={"error": str(last_error)}
            )
        )

    async def _rag_context(self, query: str) -> Optional[str]:
        if not RAG_AVAILABLE:
            return None
        try:
            has_docs = await asyncio.to_thread(rag_has_documents)
            if not has_docs:
                return None
            chunks = await asyncio.to_thread(rag_retrieve, query, settings.top_k_results)
            if not chunks:
                return None
            parts = []
            for i, chunk in enumerate(chunks, 1):
                source = chunk["source"]
                page = chunk.get("page")
                citation = f"[{source}, page {page}]" if page else f"[{source}]"
                parts.append(f"Reference {i} {citation}:\n{chunk['content']}")
            return "\n---\n".join(parts)
        except Exception as e:
            logger.warning("RAG retrieval failed: %s", e)
            return None

    # ── RAG management helpers ────────────────────────────────────────────────

    @staticmethod
    def rag_available() -> bool:
        return RAG_AVAILABLE

    @staticmethod
    async def ingest(path: str) -> bool:
        if not RAG_AVAILABLE:
            raise RuntimeError("RAG not available")
        return await asyncio.to_thread(rag_ingest, path)

    @staticmethod
    async def rag_reset() -> bool:
        if not RAG_AVAILABLE:
            raise RuntimeError("RAG not available")
        return await asyncio.to_thread(rag_db_reset)

    async def close(self):
        await self.exit_stack.aclose()
        self.sessions.clear()
