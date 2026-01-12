"""
Key Vault Service
=================
Secure storage and retrieval of API keys.

Security Model:
- Keys encrypted with Fernet (AES-128-CBC)
- SHA-256 hash stored for uniqueness checks
- Masked version for display (never expose real key)
- Original key only shown once at creation
"""

from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import APIKey, ActivityLog
from app.utils.security import SecurityUtils


class KeyVaultService:
    """
    Service for secure API key management.
    """
    
    @staticmethod
    async def get_all(session: AsyncSession) -> tuple[List[APIKey], int]:
        """Get all API keys (with masked values)."""
        count_query = select(func.count()).select_from(APIKey)
        total = (await session.execute(count_query)).scalar() or 0
        
        query = select(APIKey).order_by(APIKey.created_at.desc())
        result = await session.execute(query)
        keys = result.scalars().all()
        
        return list(keys), total
    
    @staticmethod
    async def get_by_id(session: AsyncSession, key_id: int) -> Optional[APIKey]:
        """Get a single API key by ID."""
        query = select(APIKey).where(APIKey.id == key_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(
        session: AsyncSession,
        name: str,
        value: str,
        user_id: Optional[int] = None,
    ) -> APIKey:
        """
        Store a new API key securely.
        
        The key is:
        1. Encrypted with Fernet
        2. Hashed with SHA-256 for uniqueness check
        3. Masked for display
        
        Args:
            session: Database session
            name: Service name (e.g., "OpenAI")
            value: The actual API key value
            user_id: Optional user who created this
            
        Returns:
            The created APIKey object
            
        Raises:
            ValueError if key already exists
        """
        # Check for duplicate (using hash)
        key_hash = SecurityUtils.hash_value(value)
        existing = await session.execute(
            select(APIKey).where(APIKey.key_hash == key_hash)
        )
        if existing.scalar_one_or_none():
            raise ValueError("This API key already exists")
        
        # Encrypt the key
        encrypted_value = SecurityUtils.encrypt(value)
        
        # Create masked version
        masked = SecurityUtils.mask_key(value)
        
        # Create record
        api_key = APIKey(
            name=name,
            encrypted_value=encrypted_value,
            key_hash=key_hash,
            masked=masked,
            is_active=True,
            user_id=user_id,
        )
        
        session.add(api_key)
        await session.commit()
        await session.refresh(api_key)
        
        # Log the action
        log = ActivityLog(
            user_id=user_id,
            action="create_api_key",
            details={"key_id": api_key.id, "name": name},
            status="success",
        )
        session.add(log)
        await session.commit()
        
        return api_key
    
    @staticmethod
    async def get_decrypted_value(
        session: AsyncSession,
        key_id: int,
    ) -> Optional[str]:
        """
        Get the decrypted value of an API key.
        
        USE WITH CAUTION - this exposes the actual key.
        Only use when actually needing to use the key.
        """
        api_key = await KeyVaultService.get_by_id(session, key_id)
        if not api_key or not api_key.is_active:
            return None
        
        # Update last used timestamp
        api_key.last_used_at = datetime.now(timezone.utc)
        await session.commit()
        
        # Decrypt and return
        return SecurityUtils.decrypt(api_key.encrypted_value)
    
    @staticmethod
    async def revoke(
        session: AsyncSession,
        key_id: int,
        user_id: Optional[int] = None,
    ) -> bool:
        """
        Revoke (soft delete) an API key.
        
        Sets is_active to False rather than deleting.
        This preserves audit trail.
        
        Returns True if revoked, False if not found.
        """
        api_key = await KeyVaultService.get_by_id(session, key_id)
        if not api_key:
            return False
        
        key_name = api_key.name
        api_key.is_active = False
        await session.commit()
        
        # Log the action
        log = ActivityLog(
            user_id=user_id,
            action="revoke_api_key",
            details={"key_id": key_id, "name": key_name},
            status="success",
        )
        session.add(log)
        await session.commit()
        
        return True
    
    @staticmethod
    async def delete(
        session: AsyncSession,
        key_id: int,
        user_id: Optional[int] = None,
    ) -> bool:
        """
        Permanently delete an API key.
        
        Returns True if deleted, False if not found.
        """
        api_key = await KeyVaultService.get_by_id(session, key_id)
        if not api_key:
            return False
        
        key_name = api_key.name
        await session.delete(api_key)
        await session.commit()
        
        # Log the action
        log = ActivityLog(
            user_id=user_id,
            action="delete_api_key",
            details={"key_id": key_id, "name": key_name},
            status="success",
        )
        session.add(log)
        await session.commit()
        
        return True
