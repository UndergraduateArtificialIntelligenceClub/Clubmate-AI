"""
Clubmate AI — FastAPI backend.
Run with: uvicorn api.main:app --host 0.0.0.0 --port 8000
Or via Docker Compose (recommended).
"""

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import settings
from api.routers import config, google_auth, rag, status

app = FastAPI(
    title="Clubmate AI API",
    description="Backend API for the Clubmate AI dashboard",
    version="1.0.0",
)


def _parse_frontend_origins(raw: str) -> list[str]:
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    if origins:
        return origins
    return [
        "http://frontend:3000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


# CORS — allow self-hosted frontend (Docker service + localhost for dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_frontend_origins(settings.frontend_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(status.router)
app.include_router(config.router)
app.include_router(google_auth.router)
app.include_router(rag.router)


@app.get("/")
async def root():
    return {
        "service": "Clubmate AI API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Public health check — no auth required. Used by Docker Compose healthcheck."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )
