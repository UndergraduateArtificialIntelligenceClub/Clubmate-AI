# Clubmate AI — Production Build Plan

## Overview

Self-hosted Discord bot + admin dashboard for university clubs.
Each club clones this repo and runs their own instance.
Frontend hosted on Vercel. Backend + bot self-hosted via Docker Compose.

---

## Architecture

```
Vercel (cloud)                    Club's Server (self-hosted)
──────────────────                ───────────────────────────────────
Next.js Dashboard         ←──→   FastAPI (port 8000)
  - Discord OAuth                   - Config management
  - Google account setup            - Google OAuth flow
  - RAG management                  - RAG ingestion endpoints
  - Bot settings                    - Bot status + logs
  - Role permissions                - Token storage
                                  Discord Bot
                                    - Slash commands
                                    - Role-based permissions
                                    - Meeting transcription
                                  MCP Servers
                                    - Google Calendar
                                    - Google Docs
                                    - Google Sheets
                                    - Google Forms
                                    - LibCal (UAlberta)
                                  RAG System
                                    - ChromaDB (local)
                                    - HuggingFace embeddings
                                    - Google Docs sync
                                    - File upload pipeline
```

---

## Repo Structure

```
clubmate-ai/
├── bot/
│   ├── main.py                  # Entry point
│   ├── client.py                # GeminiMCPClient (Gemini AI + MCP tool loop)
│   ├── commands/
│   │   ├── admin.py             # Exec-only slash commands
│   │   └── member.py            # Member slash commands
│   ├── events/
│   │   ├── on_message.py        # Mention handler
│   │   └── on_voice.py          # Voice channel transcription
│   └── permissions.py           # Discord role-based permission checks
│
├── api/
│   ├── main.py                  # FastAPI entry point
│   ├── routers/
│   │   ├── config.py            # Read/write config endpoints
│   │   ├── google_auth.py       # Google OAuth flow
│   │   ├── rag.py               # RAG management endpoints
│   │   └── status.py            # Bot status + health
│   └── auth.py                  # Discord OAuth verification middleware
│
├── mcp_servers/
│   ├── google_calendar.py       # Schedule, cancel, reschedule, invite, availability
│   ├── google_docs.py           # Read, create, append to docs
│   ├── google_sheets.py         # Read, write, append to sheets
│   ├── google_forms.py          # Create forms, get responses
│   └── libcal.py                # UAlberta library room availability
│
├── ragbot/
│   ├── rag.py                   # Core RAG system (ChromaDB + HuggingFace)
│   ├── config.py                # RAG config
│   ├── sources/
│   │   ├── google_docs.py       # Sync from Google Doc URL
│   │   └── file_upload.py       # Ingest uploaded files
│   └── __init__.py
│
├── frontend/                    # Next.js — deployed to Vercel
│   ├── app/
│   │   ├── page.tsx             # Landing / login
│   │   ├── dashboard/
│   │   │   ├── page.tsx         # Overview
│   │   │   ├── google/page.tsx  # Connect Google account
│   │   │   ├── rag/page.tsx     # Knowledge base management
│   │   │   ├── permissions/page.tsx  # Role config
│   │   │   └── settings/page.tsx     # API keys, bot settings
│   │   └── api/
│   │       └── auth/            # NextAuth Discord OAuth
│   ├── lib/
│   │   └── api.ts               # Typed client for FastAPI calls
│   └── ...
│
├── config/
│   └── settings.py              # Shared config (reads .env, used by bot + API)
│
├── docker-compose.yml           # Bot + API + ChromaDB
├── .env.example
└── PLAN.md                      # This file
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Discord bot | Python, discord.py, slash commands |
| AI client | Google Gemini (`google-genai`) — `gemini-2.5-flash` |
| Tool protocol | FastMCP |
| RAG | LangChain + ChromaDB + HuggingFace (`BAAI/bge-base-en-v1.5`) |
| RAG sources | Google Docs API + file upload |
| Backend API | FastAPI |
| Auth | Discord OAuth (frontend login) + Google OAuth (calendar/docs access) |
| Frontend | Next.js 14+ (App Router) |
| Frontend hosting | Vercel |
| Meeting transcription | Discord audio → OpenAI Whisper → Gemini summarize → post to channel |
| Permissions | Discord role-based, configured via dashboard |
| Deployment | Docker Compose (bot + API + ChromaDB) |

---

## Environment Variables (.env)

```env
# Discord
DISCORD_TOKEN=                   # Bot token
DISCORD_CLIENT_ID=               # For slash command registration
DISCORD_CLIENT_SECRET=           # For OAuth (frontend login verification)
DISCORD_GUILD_ID=                # The club's Discord server ID

# Gemini
GEMINI_API_KEY=

# Google OAuth (populated via dashboard)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_TOKEN_JSON=               # Path to stored token

# RAG
CHROMA_DB_DIR=./data/chroma_db
EMBEDDING_MODEL=BAAI/bge-base-en-v1.5
DEFAULT_LLM_MODEL=gemini-2.5-flash
TOP_K_RESULTS=5

# API
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=                  # For signing JWT sessions

# Frontend (set in Vercel env vars)
NEXT_PUBLIC_API_URL=             # URL of the club's self-hosted FastAPI
NEXTAUTH_SECRET=
NEXTAUTH_URL=
```

---

## Build Phases

### Phase 1 — Repo Restructure + Config (START HERE)
- Create new folder layout
- Shared `config/settings.py` (Pydantic Settings, reads .env)
- `.env.example` with all variables
- `requirements.txt` split: `bot`, `api`, `rag`, `mcp`

### Phase 2 — MCP Servers
- Port `calendar_integration.py` → `mcp_servers/google_calendar.py` (clean up duplicated code)
- Port `libcal_server.py` → `mcp_servers/libcal.py` (as-is, it works)
- New: `mcp_servers/google_docs.py`
- New: `mcp_servers/google_sheets.py`
- New: `mcp_servers/google_forms.py`

### Phase 3 — Bot Rewrite
- Slash commands (replace `!prefix`)
- Role-based permission checks (exec role from config)
- Connect all MCP servers on startup
- Meeting transcription: join voice → Whisper → Gemini → post summary

### Phase 4 — RAG Refactor
- Keep core `RAGSystem` (it's good)
- Add `ragbot/sources/google_docs.py` — fetch Google Doc content, ingest into ChromaDB
- Add `ragbot/sources/file_upload.py` — receive file bytes from API, ingest

### Phase 5 — FastAPI Backend
- `/config` — read/write `.env` settings
- `/google/auth` — initiate Google OAuth flow, store token
- `/rag/ingest` — trigger ingestion (Google Doc URL or file upload)
- `/rag/reset` — clear ChromaDB
- `/status` — bot online status, connected servers, doc count
- Discord OAuth middleware — verify dashboard user is a guild admin

### Phase 6 — Next.js Frontend (Vercel)
- Login with Discord (NextAuth)
- Dashboard: bot status overview
- Google account connection page (triggers OAuth on the API)
- Knowledge base page (add Google Doc URL, upload files, view ingested docs)
- Permissions page (set exec role)
- Settings page (API keys, model selection, active MCP servers)

### Phase 7 — Docker Compose
- Service: `bot` (Python)
- Service: `api` (FastAPI / uvicorn)
- Volume: `./data/chroma_db` persisted
- Single `docker compose up` starts everything

---

## Key Design Decisions

1. **Gemini is the only AI client** — no LangChain LLM wrappers for chat, only for RAG embeddings
2. **LibCal stays as-is** — the existing API scraping works, just relocated
3. **Google OAuth via dashboard** — no more `python authenticate.py` in terminal
4. **Slash commands** — replaces `!prefix` commands, native Discord permission system
5. **Role permissions** — exec role set in dashboard, enforced in bot via `permissions.py`
6. **Vercel frontend → self-hosted API** — clubs need a publicly reachable backend (VPS or Cloudflare Tunnel)
7. **All tokens stay on club's server** — Vercel never sees Google tokens or API keys
8. **Meeting transcription** — discord.py voice receive + Whisper (local or API) + Gemini summary
