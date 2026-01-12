"""
Contacts Router
===============
API endpoints for contact management.

Endpoints:
- GET /contacts/ - List all contacts
- POST /contacts/ - Create new contact
- GET /contacts/{id} - Get single contact
- PUT /contacts/{id} - Update contact
- DELETE /contacts/{id} - Delete contact
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.contact import (
    ContactCreate,
    ContactUpdate,
    ContactResponse,
)
from app.services.contact_service import ContactService


router = APIRouter()


@router.get("/", response_model=List[ContactResponse])
async def list_contacts(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    session: AsyncSession = Depends(get_session),
):
    """
    List all contacts with pagination.
    
    Query params:
    - skip: Number of records to skip (default: 0)
    - limit: Max records to return (default: 100, max: 500)
    """
    contacts, total = await ContactService.get_all(session, skip=skip, limit=limit)
    return contacts


@router.post("/", response_model=ContactResponse, status_code=201)
async def create_contact(
    data: ContactCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new contact.
    
    Required fields:
    - name: Contact's full name
    
    Optional fields:
    - email, phone, discord_id, discord_username, notes, tags
    """
    contact = await ContactService.create(session, data)
    return contact


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a single contact by ID."""
    contact = await ContactService.get_by_id(session, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    data: ContactUpdate,
    session: AsyncSession = Depends(get_session),
):
    """
    Update an existing contact.
    
    All fields are optional - only provided fields will be updated.
    """
    contact = await ContactService.update(session, contact_id, data)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", status_code=204)
async def delete_contact(
    contact_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Delete a contact by ID."""
    deleted = await ContactService.delete(session, contact_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Contact not found")
    return None
