# Clubmate-AI

AI-powered Discord bot with RAG (Retrieval-Augmented Generation) and MCP (Model Context Protocol) integration.

## Features

- 🤖 **Chat with Gemini AI** — Conversational AI with tool use
- 📚 **RAG Knowledge Base** — Ingest documents (PDF, TXT, MD) for contextual Q&A
- 📅 **Google Calendar** — View and manage events via MCP
- 🔧 **Extensible MCP Servers** — Add custom tools easily

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure

```bash
# Copy and edit .env
cp .env.example .env
# Add your DISCORD_TOKEN, GEMINI_API_KEY
```

### 3. Run

```bash
python gemini/discord_bot.py
```

---

## Discord Commands

### Chat & AI
| Command | Description |
|---------|-------------|
| `!chat <message>` | Chat with Gemini AI |
| `@Clubmate-AI <message>` | Mention to chat |
| `!clear` | Clear conversation history |

### RAG (Knowledge Base)
| Command | Description |
|---------|-------------|
| `!ingest <path>` | Ingest documents into knowledge base |
| `!rag-reset` | Clear all ingested documents |

### MCP Servers
| Command | Description |
|---------|-------------|
| `!servers` | List configured MCP servers |
| `!connect <name>` | Connect to a server (e.g., `!connect calendar`) |
| `!tools` | List available tools |

---

## RAG Testing

```bash
# Test RAG system
python test_rag.py status         # Check status
python test_rag.py ingest <path>  # Ingest documents
python test_rag.py query "..."    # Query with LLM
python test_rag.py retrieve "..." # Raw retrieval (no LLM)
python test_rag.py reset          # Clear database

# Verbose mode
python test_rag.py status -v
```

---

## Configuration

### Google Calendar API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable **Google Calendar API**
3. Create OAuth credentials (Desktop app)
4. Save as `credentials.json` in project root
5. Run `python src/authenticate.py` to generate `token.json`

### Environment Variables (`.env`)
```
DISCORD_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_gemini_api_key
CHROMA_DB_DIR=./ragbot/chroma_db
EMBEDDING_MODEL=BAAI/bge-base-en-v1.5
DEFAULT_LLM_MODEL=gemini-2.5-flash-lite
```

---

## Project Structure

```
Clubmate-AI/
├── gemini/              # Discord bot & MCP client
│   ├── discord_bot.py   # Main bot entry point
│   ├── gemini_mcp_client.py
│   └── example_server.py
├── ragbot/              # RAG module
│   ├── rag.py           # Core RAG functionality
│   └── config.py        # RAG configuration
├── src/
│   └── servers/         # MCP servers
│       └── calendar_integration.py
├── test_rag.py          # RAG test script
└── .env.example         # Environment template
```

---

*Developed by the Undergraduate Artificial Intelligence Club*