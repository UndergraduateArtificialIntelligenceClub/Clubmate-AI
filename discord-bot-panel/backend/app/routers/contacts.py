from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models.contact import Contact
from app.auth.dependencies import get_current_admin
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/contacts", tags=["Contacts"])


class ContactCreate(BaseModel):
    username: str
    discord_id: str
    roles: List[str] = []
    status: str = "active"
    notes: Optional[str] = None


@router.get("/")
async def list_contacts(
    session: AsyncSession = Depends(get_session), user=Depends(get_current_admin)
):
    stmt = select(Contact).order_by(Contact.created_at.desc())
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("/")
async def create_contact(
    contact: ContactCreate,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_admin),
):
    # Check for existing
    stmt = select(Contact).where(Contact.discord_id == contact.discord_id)
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Contact exists")

    new_contact = Contact(
        username=contact.username,
        discord_id=contact.discord_id,
        roles=contact.roles,
        status=contact.status,
        notes=contact.notes,
    )
    session.add(new_contact)
    await session.commit()
    await session.refresh(new_contact)
    return new_contact


@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: int,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_admin),
):
    contact = await session.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    await session.delete(contact)
    await session.commit()
    return {"status": "deleted"}
