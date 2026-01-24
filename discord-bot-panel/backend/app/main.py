"""
FastAPI Application Entry Point
===============================
Main application file that bootstraps the FastAPI server.

This file handles:
- Application lifecycle (startup/shutdown)
- Middleware stack configuration
- Router registration
- CORS configuration
- Health check endpoint
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db, close_db

# Import routers
from app.routers import (
    auth,
    contacts,
    files,
    api_keys,
    stats,
    setup,
)

settings = get_settings()


# ============================================================
# APPLICATION LIFECYCLE
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Manage application startup and shutdown events.
    
    Startup:
    - Initialize database connection pool
    - Create tables if they don't exist (dev only)
    - Initialize any background services
    
    Shutdown:
    - Close database connections gracefully
    - Cleanup any resources
    """
    # Startup
    print("🚀 Starting Clubmate Bot Panel API...")
    
    # Initialize database (creates tables in dev mode)
    if settings.debug:
        await init_db()
        print("📦 Database tables initialized")
    
    # Create upload directory if it doesn't exist
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    print(f"📁 Upload directory: {settings.upload_path}")
    
    yield  # Application runs here
    
    # Shutdown
    print("🛑 Shutting down...")
    await close_db()
    print("✅ Database connections closed")


# ============================================================
# APPLICATION FACTORY
# ============================================================
def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Using a factory pattern allows for:
    - Multiple app instances (testing)
    - Cleaner configuration management
    - Easier dependency injection
    """
    app = FastAPI(
        title="Clubmate Bot Panel API",
        description="Backend API for Discord Bot Admin Panel",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,  # Disable docs in production
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # ============================================================
    # CORS MIDDLEWARE
    # ============================================================
    # Required for frontend (localhost:5173) to communicate with backend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,  # Required for cookies/auth
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ============================================================
    # ROUTER REGISTRATION
    # ============================================================
    # All routers prefixed with /api for clean URL structure
    app.include_router(auth.router, prefix=f"{settings.api_prefix}/auth", tags=["Authentication"])
    app.include_router(contacts.router, prefix=f"{settings.api_prefix}/contacts", tags=["Contacts"])
    app.include_router(files.router, prefix=f"{settings.api_prefix}/files", tags=["Files"])
    app.include_router(api_keys.router, prefix=f"{settings.api_prefix}/api-keys", tags=["API Keys"])
    app.include_router(stats.router, prefix=f"{settings.api_prefix}/stats", tags=["Statistics"])
    app.include_router(setup.router, prefix=f"{settings.api_prefix}/setup", tags=["Setup"])
    
    # ============================================================
    # HEALTH CHECK
    # ============================================================
    @app.get("/health", tags=["Health"])
    async def health_check():
        """
        Health check endpoint for load balancers and monitoring.
        
        Returns 200 OK if the service is running.
        Does NOT check database connectivity (use /ready for that).
        """
        return {"status": "healthy", "version": "1.0.0"}
    
    @app.get("/", tags=["Health"])
    async def root():
        """Root endpoint with API info."""
        return {
            "name": "Clubmate Bot Panel API",
            "version": "1.0.0",
            "docs": "/docs" if settings.debug else "disabled",
        }
    
    return app


# Create the app instance
app = create_app()
