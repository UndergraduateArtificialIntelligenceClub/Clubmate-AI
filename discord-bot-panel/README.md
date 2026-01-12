# Clubmate Bot Panel

A production-grade admin panel for managing Discord bot operations, built with FastAPI (Python) and React.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                             │
│  React + Vite (localhost:5173)                              │
│  ┌──────┬──────┬───────┬─────────┬──────────┐             │
│  │Dash  │Conts │Files  │API Keys │Google    │             │
│  └──────┴──────┴───────┴─────────┴──────────┘             │
└─────────────────────────────────────────────────────────────┘
                            │ HTTP/JSON
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend API                            │
│  FastAPI (localhost:8000)                                   │
│  ┌────────────────────────────────────────────────────────┐│
│  │ Routers → Services → Models → Database                 ││
│  └────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                            │
          ┌─────────────────┴─────────────────┐
          ▼                                   ▼
   ┌──────────────┐                   ┌──────────────┐
   │  PostgreSQL  │                   │  File System │
   │  (contacts,  │                   │  (uploads/)  │
   │   files,     │                   └──────────────┘
   │   api_keys,  │
   │   logs)      │
   └──────────────┘
```

## ✨ Features

- **Contacts Management** - Store contacts with name, email, phone, Discord, and tags
- **File Storage** - Upload/download PDFs, Excel, docs with metadata tracking
- **API Key Vault** - Encrypted storage for third-party API keys (Fernet AES-128)
- **Activity Logs** - Full audit trail of all actions
- **Google OAuth** - Connect Google Drive/Gmail
- **Dashboard** - Real-time stats and activity feed

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ (or Docker)
- pnpm (recommended) or npm

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd discord-bot-panel

# Copy environment template
cp .env.example .env
# Edit .env with your credentials
```

### 2. Database Setup

**Option A: Docker (Recommended)**
```bash
docker-compose up -d
```

**Option B: Local PostgreSQL**
```bash
createdb clubmate
# Update DATABASE_URL in .env
```

### 3. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Navigate to backend
cd backend

# Run database migrations
alembic upgrade head

# (Optional) Seed sample data
python -m scripts.seed

# Start the server
uvicorn app.main:app --reload --port 8000
```

### 4. Frontend Setup

```bash
# In a new terminal
cd frontend

# Install dependencies
pnpm install

# Start dev server
pnpm dev
```

### 5. Access the Application

- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📁 Project Structure

```
discord-bot-panel/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI entry point
│   │   ├── config.py         # Configuration management
│   │   ├── database.py       # Database connection
│   │   ├── models/           # SQLModel ORM models
│   │   ├── schemas/          # Pydantic request/response
│   │   ├── routers/          # API route handlers
│   │   ├── services/         # Business logic
│   │   └── utils/            # Helpers (encryption, etc.)
│   ├── alembic/              # Database migrations
│   ├── uploads/              # File storage
│   └── scripts/              # Utility scripts
├── frontend/
│   └── src/
│       ├── pages/            # Page components
│       ├── components/       # Reusable components
│       └── services/         # API client
└── requirements.txt
```

## 🔒 Security

| Feature | Implementation |
|---------|---------------|
| API Key Storage | Fernet encryption (AES-128-CBC) |
| OAuth Tokens | Encrypted at rest |
| File Uploads | Extension whitelist, size limits |
| SQL Injection | SQLAlchemy parameterized queries |
| CORS | Strict origin whitelist |

### Generate Encryption Key

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

## 📊 Database Schema

| Table | Purpose |
|-------|---------|
| `users` | Admin accounts (Discord OAuth) |
| `contacts` | General contact storage |
| `files` | Uploaded file metadata |
| `api_keys` | Encrypted API key storage |
| `activity_logs` | Audit trail |
| `oauth_tokens` | Google OAuth credentials |

## 🔧 Configuration

All configuration via environment variables (see `.env.example`):

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing key |
| `ENCRYPTION_KEY` | Fernet key for API key encryption |
| `GOOGLE_CLIENT_ID/SECRET` | Google OAuth credentials |
| `DISCORD_CLIENT_ID/SECRET` | Discord OAuth credentials |

## 📝 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/contacts/` | GET, POST | List/create contacts |
| `/api/contacts/{id}` | GET, PUT, DELETE | Contact CRUD |
| `/api/files/` | GET | List files |
| `/api/files/upload` | POST | Upload file |
| `/api/files/{id}` | GET, DELETE | File operations |
| `/api/api-keys/` | GET, POST | List/create API keys |
| `/api/api-keys/{id}` | DELETE | Revoke key |
| `/api/stats/` | GET | Dashboard statistics |
| `/api/stats/logs` | GET, DELETE | Activity logs |
| `/api/auth/google/*` | - | Google OAuth flow |

## 🔄 Development

### Running Migrations

```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Running Tests

```bash
cd backend
pytest tests/ -v
```

## 📦 Deployment

For production deployment:

1. Set `ENVIRONMENT=production` and `DEBUG=false`
2. Use a proper secret key (`openssl rand -hex 32`)
3. Configure PostgreSQL with SSL
4. Set up reverse proxy (nginx)
5. Enable HTTPS

## 📄 License

MIT
