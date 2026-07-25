# Clubmate AI

Clubmate AI is a Discord bot + dashboard for student clubs.

It provides:
- Discord slash-command assistant powered by Gemini
- Google Calendar / Docs / Sheets / Forms actions via MCP tools
- RAG knowledge base (file + Google Doc ingestion)
- Meeting voice recording, transcription, and summary posting
- Web dashboard for admin configuration and Google connection

## Architecture

This repo runs 3 services:
- `bot`: Discord bot (`python -m bot.main`)
- `api`: FastAPI backend (`http://localhost:8000`)
- `frontend`: Next.js dashboard (`http://localhost:3000`)

The recommended way to run is Docker Compose.

## Prerequisites

Install:
- Docker Desktop + Docker Compose
- A Discord application + bot token
- A Gemini API key
- A Google Cloud project (for Calendar/Docs/Sheets/Forms OAuth)

## 1. Clone and Configure Environment

From project root:

```bash
cp .env.example .env
cp frontend/.env.local.example frontend/.env.local
```

Set values in `.env`:
- `DISCORD_TOKEN`
- `DISCORD_CLIENT_ID`
- `DISCORD_CLIENT_SECRET`
- `DISCORD_GUILD_ID`
- `GEMINI_API_KEY`
- `API_SECRET_KEY` (generate a strong random value)

Optional but recommended:
- `EXEC_ROLE_NAME` (default `Executive`)
- `MEETING_SUMMARY_CHANNEL_ID`
- `WHISPER_MODE` (`local` or `api`)
- `OPENAI_API_KEY` (only if `WHISPER_MODE=api`)

Set values in `frontend/.env.local`:
- `NEXTAUTH_SECRET`
- `NEXTAUTH_URL=http://localhost:3000`
- `DISCORD_CLIENT_ID` (same as root `.env`)
- `DISCORD_CLIENT_SECRET` (same as root `.env`)
- `NEXT_PUBLIC_API_URL=http://localhost:8000`

## 2. Discord OAuth Setup

In Discord Developer Portal:

1. Open your application.
2. Add OAuth redirect URI:
   - `http://localhost:3000/api/auth/callback/discord`
3. Enable required bot permissions in your server.
4. Invite the bot to the target server (`DISCORD_GUILD_ID`).

## 3. Google Cloud OAuth Setup

In Google Cloud Console for the same project:

1. Enable APIs:
   - Google Calendar API
   - Google Docs API
   - Google Sheets API
   - Google Forms API
   - Google Drive API
2. Configure OAuth consent screen:
   - User type: External (or Internal for Workspace)
   - Publishing status: Testing is fine for development
   - Add your account as a Test User
3. Create OAuth Client ID:
   - Application type: Web application
   - Authorized redirect URI:
     - `http://localhost:8000/google/callback`
   - Authorized JavaScript origins: optional for this backend callback flow
4. Use the dashboard Google page to upload credentials JSON and complete auth.

## 4. Start the Stack

```bash
docker compose up -d --build
```

Check health:

```bash
curl http://localhost:8000/health
```

Open dashboard:
- `http://localhost:3000`

## 5. First-Time Dashboard Flow

1. Sign in with Discord (must have Manage Server/Admin in target guild).
2. Go to Settings and verify API keys/config.
3. Go to Google page:
   - Upload OAuth credentials JSON
   - Click connect and finish OAuth
4. Go to Knowledge Base:
   - Upload files or sync Google Doc

## Discord Commands

### Member commands
- `/ask`
- `/events` (today by default, or pass date)
- `/rooms`
- `/clear`
- `/help`

### Exec commands
- `/schedule`, `/cancel-meeting`, `/reschedule`, `/invite`
- `/day-schedule`, `/cancel-day`, `/reschedule-day`, `/invite-day`
- `/create-doc`, `/create-form`, `/form-responses`, `/read-sheet`
- `/ingest`, `/kb-reset`
- `/meeting start`, `/meeting end`

## RAG Notes

- Database path: `data/chroma_db`
- Google Doc ingestion requires Google account connection and Docs API enabled
- If chunk count is `0`, document may be empty, inaccessible, or too short

## Meeting Transcription Notes

- `WHISPER_MODE=local`: uses local Whisper model in container
- `WHISPER_MODE=api`: uses OpenAI Whisper API
- Summaries are posted to the meeting summary channel

## Troubleshooting

### `403 PERMISSION_DENIED` / leaked API key
Your Gemini key was revoked. Create a new key and update `GEMINI_API_KEY`.

### Google OAuth `access_denied` in testing
Add your account under OAuth consent screen Test Users.

### Google callback `invalid_grant` / `Missing code verifier`
Restart OAuth from dashboard and complete in one browser session.

### `Google Docs API ... is disabled`
Enable Google Docs API in the same Google Cloud project used by OAuth credentials.

### Frontend "Server error"
Check:
- API is healthy: `curl http://localhost:8000/health`
- `NEXT_PUBLIC_API_URL` points to `http://localhost:8000`
- Discord OAuth vars are set in `frontend/.env.local`

### Restart services
```bash
docker compose restart api bot frontend
```

### Stop services
```bash
docker compose down
```

## Security

Never commit:
- `.env`
- `data/google_credentials.json`
- `data/google_token.json`

If any secret was exposed, rotate it immediately.
