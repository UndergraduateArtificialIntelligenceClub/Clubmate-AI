# Clubmate AI

Clubmate AI is a Discord bot + web dashboard for student clubs.  
It combines:
- Discord slash commands and chat
- Google Workspace integrations (Calendar, Docs, Sheets, Forms)
- RAG knowledge base (file + Google Doc ingestion)
- Meeting voice transcription + AI summaries

This repository contains the full stack:
- `bot` (Discord bot)
- `api` (FastAPI backend)
- `frontend` (Next.js dashboard)

## System Architecture

- `frontend` (port `3000`): Admin dashboard, Discord OAuth sign-in via NextAuth.
- `api` (port `8000`): Authz, Google OAuth endpoints, config management, RAG ingestion/status.
- `bot`: Discord bot process, MCP tool orchestration, voice meeting recording/transcription.
- `data/`: Persistent runtime data (`chroma_db`, Google OAuth token/credentials JSON).

The recommended way to run is Docker Compose.

## Core Features

- Discord member commands (`/ask`, `/events`, `/rooms`, `/help`, ...)
- Exec-only commands for scheduling and admin workflows
- Day-specific meeting management:
  - `/day-schedule`
  - `/cancel-day`
  - `/reschedule-day`
  - `/invite-day`
- Knowledge base ingestion from:
  - Uploaded files (`.pdf`, `.txt`, `.md`)
  - Google Docs URLs
- Meeting recording:
  - `/meeting start`
  - `/meeting end`
  - Summary posted to Discord
  - Transcript saved to Google Doc with link posted in Discord

## Prerequisites

- Docker Desktop (or Docker Engine + Compose v2)
- A Discord application + bot
- A Gemini API key
- (Optional but recommended) Google Cloud project for Calendar/Docs/Sheets/Forms

## 1) Clone And Configure

```bash
git clone <your-repo-url>
cd Clubmate-AI
cp .env.example .env
```

Generate a NextAuth secret:

```bash
openssl rand -base64 32
```

Paste that value into `NEXTAUTH_SECRET` in `.env`.

## 2) Discord Setup (Required)

### 2.1 Create app + bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications).
2. Create an application.
3. Open `Bot` tab and create/reset bot token.
4. Copy:
   - Bot token -> `DISCORD_TOKEN`
   - Application ID -> `DISCORD_CLIENT_ID`
   - Client Secret -> `DISCORD_CLIENT_SECRET`

### 2.2 Bot intents

In `Bot` settings, enable:
- `Message Content Intent`

### 2.3 Invite bot to your server

In `OAuth2 > URL Generator`:
- Scopes: `bot`, `applications.commands`
- Bot permissions (minimum practical set):
  - View Channels
  - Send Messages
  - Embed Links
  - Read Message History
  - Use Application Commands
  - Connect
  - Speak

Open generated URL and invite the bot to your target server.

### 2.4 Get server (guild) ID

Enable Discord Developer Mode, right-click your server, copy ID:
- `DISCORD_GUILD_ID=<your-server-id>`

### 2.5 Dashboard Discord OAuth redirect

For dashboard login, add this redirect URI in Discord `OAuth2 > Redirects`:
- Local: `http://localhost:3000/api/auth/callback/discord`
- Production: `https://<your-frontend-domain>/api/auth/callback/discord`

## 3) Gemini Setup (Required)

1. Create API key at [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Set:
   - `GEMINI_API_KEY=<your-key>`

If the key gets revoked/leaked, generate a new key and update dashboard/API keys.

## 4) Environment Variables (Required Minimum)

In `/Users/sashreek/Documents/Clubmate-AI/.env`, set at least:

```env
DISCORD_TOKEN=
DISCORD_CLIENT_ID=
DISCORD_CLIENT_SECRET=
DISCORD_GUILD_ID=
GEMINI_API_KEY=
NEXTAUTH_SECRET=
NEXTAUTH_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Environment source of truth:
- Docker Compose reads from the root `.env` file.
- `frontend/.env.local` is only for standalone frontend development (`npm run dev` in `frontend`).

Also strongly recommended for security:

```env
API_SECRET_KEY=<random-hex-string>
```

Generate one:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## 5) Start The Stack

```bash
docker compose up -d --build
```

Check status:

```bash
docker compose ps
docker compose logs --tail=100 api bot frontend
```

Open dashboard:
- `http://localhost:3000`

Health check:
- `http://localhost:8000/health`

## 6) Google Integration Setup (Calendar/Docs/Sheets/Forms)

This enables scheduling commands, Google Doc ingestion, form/sheet features, and transcript doc writing.

### 6.1 Google Cloud project

1. Create/select project in [Google Cloud Console](https://console.cloud.google.com/).
2. Enable APIs:
   - Google Calendar API
   - Google Docs API
   - Google Sheets API
   - Google Forms API
   - Google Drive API

### 6.2 OAuth consent screen

1. Configure OAuth consent screen.
2. If app is in testing mode, add your Google account under **Test users**.

### 6.3 Create OAuth client credentials

1. `APIs & Services > Credentials > Create Credentials > OAuth client ID`
2. Application type: **Web application**
3. Authorized redirect URIs:
   - Local: `http://localhost:8000/google/callback`
   - Production: `https://<your-api-domain>/google/callback`
4. Authorized JavaScript origins: optional for this backend-driven flow.
5. Download the credentials JSON.

### 6.4 Connect Google in dashboard

1. Go to Dashboard -> `Google Account`.
2. Upload downloaded credentials JSON.
3. Click connect and complete Google OAuth.

## 7) Knowledge Base (RAG) Setup

Dashboard -> `Knowledge Base`:
- Upload files (`.pdf`, `.txt`, `.md`)
- Or sync a Google Doc URL

Then members can query content via `/ask`.

Notes:
- If Google Doc ingestion returns 400/403, check:
  - Google account is connected
  - Doc is accessible to that account
  - Google Docs API is enabled in your Google project
- Very short/empty docs may not produce semantic chunks.

## 8) Command Reference

### Member commands

- `/ask`
- `/events [date]`
- `/rooms [library] [date]`
- `/clear`
- `/help`

### Exec-only commands

- `/schedule`
- `/cancel-meeting`
- `/reschedule`
- `/invite`
- `/day-schedule`
- `/cancel-day`
- `/reschedule-day`
- `/invite-day`
- `/create-doc`
- `/create-form`
- `/form-responses`
- `/read-sheet`
- `/ingest`
- `/kb-reset`
- `/meeting start`
- `/meeting end`

Set exec role in dashboard `Permissions` page (`EXEC_ROLE_NAME`).

## 9) Meeting Recording + Transcription

- Start in a voice channel with `/meeting start`.
- End with `/meeting end`.
- Bot behavior:
  - Captures voice audio
  - Transcribes and summarizes
  - Posts summary in configured summary channel
  - Saves full transcript to Google Doc and posts the link

Relevant env/config:
- `MEETING_SUMMARY_CHANNEL_ID`
- `WHISPER_MODE`:
  - `gemini` (default, recommended)
  - `local` (local Whisper model, CPU heavy)
  - `api` (OpenAI Whisper API, requires `OPENAI_API_KEY`)

## 10) Deploy For Club Members (Remote Access)

If members need to access dashboard from other devices, do not use localhost URLs in production.

Set in `.env`:

```env
NEXTAUTH_URL=https://<frontend-domain>
NEXT_PUBLIC_API_URL=https://<api-domain>
API_EXTERNAL_BASE_URL=https://<api-domain>
FRONTEND_ORIGINS=https://<frontend-domain>
```

Then rebuild:

```bash
docker compose up -d --build
```

Important:
- `NEXT_PUBLIC_API_URL` is baked at frontend build time. Rebuild frontend whenever it changes.
- `localhost` only works from the machine running containers.

## 11) Operations

Rebuild/restart all services:

```bash
docker compose up -d --build
```

Restart only bot after key/config updates:

```bash
docker compose restart bot
```

Follow logs:

```bash
docker compose logs -f bot
docker compose logs -f api
docker compose logs -f frontend
```

## 12) Troubleshooting

### Docker daemon not running

Symptom:
- `Cannot connect to the Docker daemon ...`

Fix:
- Start Docker Desktop/daemon and rerun compose commands.

### Invalid Discord token

Symptom:
- Bot log: `discord.errors.LoginFailure: Improper token has been passed.`

Fix:
- Regenerate bot token in Discord Developer Portal.
- Update `DISCORD_TOKEN`.
- `docker compose restart bot`

### Dashboard says session expired/invalid

Symptom:
- API response indicates invalid dashboard session.

Fix:
- Sign out/in again via Discord.
- Verify `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`, and Discord OAuth redirect URI.

### Google OAuth access blocked (403 access_denied)

Fix:
- Add your account as OAuth test user in Google consent screen.
- Ensure you are using the same Google project that owns the OAuth client.

### Google Docs API disabled

Symptom:
- Ingestion error says Docs API has not been used or is disabled.

Fix:
- Enable Google Docs API in that exact project, wait a few minutes, retry.

### RAG returns zero chunks or cannot retrieve

Fix:
- Re-ingest docs from dashboard.
- If database is corrupted/stale, clear via dashboard (`Clear all`) and re-ingest.

### Bot responses are slow initially

Reason:
- First request warms MCP sessions + RAG.

Fix:
- Wait for pre-warm completion; subsequent requests are faster.

## 13) Security Notes

- Never commit:
  - `.env`
  - `data/google_token.json`
  - `data/google_credentials.json`
- Rotate any leaked keys immediately (Discord, Gemini, OpenAI, Google OAuth).
- Use strong `API_SECRET_KEY` and `NEXTAUTH_SECRET` in production.

## 14) Project Layout

```text
Clubmate-AI/
├── api/                  # FastAPI backend (auth, config, Google OAuth, RAG endpoints)
├── bot/                  # Discord bot, commands, voice meeting pipeline
├── config/               # Shared settings loader
├── frontend/             # Next.js dashboard (Discord sign-in, admin UI)
├── mcp_servers/          # Google + LibCal MCP tool servers
├── ragbot/               # Embeddings, chunking, retrieval, ingestion
├── data/                 # Runtime data (chroma DB, OAuth tokens)
├── docker-compose.yml
└── .env.example
```
