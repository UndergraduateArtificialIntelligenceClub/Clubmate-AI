from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    auth,
    api_keys,
    files,
    contacts,
    google_auth,
    stats,
)  # Added stats
from app.db.session import init_db
import os

app = FastAPI(title="Discord Bot Panel")

# CORS setup for development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all Routers
app.include_router(auth.router, prefix="/api")
app.include_router(api_keys.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")
app.include_router(google_auth.router, prefix="/api")
app.include_router(stats.router, prefix="/api")  # Added this line


@app.on_event("startup")
async def on_startup():
    print("Initializing Database...")
    await init_db()
    # Ensure upload dirs exist
    os.makedirs("../storage/uploads", exist_ok=True)
    print("Database Ready.")

app.mount("/storage", StaticFiles(directory="../storage"), name="storage")



@app.get("/health")
def health_check():
    return {"status": "ok", "db": "connected"}
