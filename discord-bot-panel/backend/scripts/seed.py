"""
Seed Data Script
================
Populates the database with initial sample data for development.

Run with: python -m scripts.seed
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_session_context
from app.models import User, Contact, APIKey, ActivityLog
from app.utils.security import SecurityUtils


async def seed_users():
    """Create sample admin users."""
    users = [
        User(
            discord_id="123456789012345678",
            username="admin",
            email="admin@example.com",
            role=0,  # Admin
            is_active=True,
        ),
        User(
            discord_id="987654321098765432",
            username="member",
            email="member@example.com",
            role=1,  # Member
            is_active=True,
        ),
    ]
    
    async with get_session_context() as session:
        for user in users:
            session.add(user)
        print(f"✓ Created {len(users)} users")


async def seed_contacts():
    """Create sample contacts."""
    contacts = [
        Contact(
            name="John Doe",
            email="john.doe@example.com",
            phone="+1-555-123-4567",
            discord_id="111111111111111111",
            discord_username="johndoe",
            notes="Club president 2024-2025",
            tags=["member", "executive"],
        ),
        Contact(
            name="Jane Smith",
            email="jane.smith@university.edu",
            phone="+1-555-987-6543",
            discord_username="janesmith",
            notes="Event coordinator",
            tags=["member", "volunteer"],
        ),
        Contact(
            name="Bob Wilson",
            email="bob@sponsor.com",
            phone="+1-555-555-5555",
            notes="Sponsor contact from TechCorp",
            tags=["sponsor", "external"],
        ),
    ]
    
    async with get_session_context() as session:
        for contact in contacts:
            session.add(contact)
        print(f"✓ Created {len(contacts)} contacts")


async def seed_api_keys():
    """Create sample API keys (encrypted)."""
    keys = [
        ("OpenAI", "sk-demo1234567890abcdefghijklmnopqrstuvwxyz"),
        ("Discord Bot", "MTIzNDU2Nzg5MDEyMzQ1Njc4.ABcDeF.abcdefghijklmnopqrstuvwxyz1234567890"),
    ]
    
    async with get_session_context() as session:
        for name, value in keys:
            api_key = APIKey(
                name=name,
                encrypted_value=SecurityUtils.encrypt(value),
                key_hash=SecurityUtils.hash_value(value),
                masked=SecurityUtils.mask_key(value),
                is_active=True,
            )
            session.add(api_key)
        print(f"✓ Created {len(keys)} API keys")


async def seed_activity_logs():
    """Create sample activity logs."""
    logs = [
        ActivityLog(
            user_id=1,
            action="login",
            details={"method": "discord_oauth"},
            status="success",
        ),
        ActivityLog(
            user_id=1,
            action="create_contact",
            details={"contact_name": "John Doe"},
            status="success",
        ),
        ActivityLog(
            user_id=1,
            action="upload_file",
            details={"filename": "meeting_notes.pdf", "size": 102400},
            status="success",
        ),
    ]
    
    async with get_session_context() as session:
        for log in logs:
            session.add(log)
        print(f"✓ Created {len(logs)} activity logs")


async def main():
    """Run all seed functions."""
    print("🌱 Seeding database...")
    print("-" * 40)
    
    await seed_users()
    await seed_contacts()
    await seed_api_keys()
    await seed_activity_logs()
    
    print("-" * 40)
    print("✅ Seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())
