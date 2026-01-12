"""
API Keys Router
===============
API endpoints for secure API key management.

Endpoints:
- GET /api-keys/ - List all keys (masked values)
- POST /api-keys/ - Create new key
- DELETE /api-keys/{id} - Revoke/delete key
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.api_key import APIKeyCreate, APIKeyResponse
from app.services.key_vault_service import KeyVaultService


router = APIRouter()


@router.get("/", response_model=List[APIKeyResponse])
async def list_api_keys(
    session: AsyncSession = Depends(get_session),
):
    """
    List all API keys.
    
    Note: Returns masked values only - the actual key is never exposed
    after initial creation.
    """
    keys, total = await KeyVaultService.get_all(session)
    return keys


@router.post("/", response_model=APIKeyResponse, status_code=201)
async def create_api_key(
    data: APIKeyCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Store a new API key securely.
    
    Required fields:
    - name: Service name (e.g., "OpenAI API Key")
    - value: The actual API key
    
    IMPORTANT: The actual key value is encrypted and will NOT be returned
    after this request. Store it safely.
    """
    try:
        api_key = await KeyVaultService.create(
            session,
            name=data.name,
            value=data.value,
        )
        return api_key
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{key_id}", status_code=204)
async def delete_api_key(
    key_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Revoke/delete an API key.
    
    This permanently removes the key from the system.
    """
    deleted = await KeyVaultService.delete(session, key_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="API key not found")
    return None
