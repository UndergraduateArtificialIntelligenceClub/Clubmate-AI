"""
Contact Service
===============
Business logic for contact management.

Handles CRUD operations on contacts with proper validation
and database session management.
"""

from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contact, ActivityLog
from app.schemas.contact import ContactCreate, ContactUpdate


class ContactService:
    """
    Service class for contact operations.
    
    All methods are static and accept a database session.
    This allows for easy testing and transaction control.
    """
    
    @staticmethod
    async def get_all(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Contact], int]:
        """
        Get all contacts with pagination.
        
        Returns:
            Tuple of (contacts list, total count)
        """
        # Get total count
        count_query = select(func.count()).select_from(Contact)
        total = (await session.execute(count_query)).scalar() or 0
        
        # Get paginated contacts
        query = (
            select(Contact)
            .order_by(Contact.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(query)
        contacts = result.scalars().all()
        
        return list(contacts), total
    
    @staticmethod
    async def get_by_id(session: AsyncSession, contact_id: int) -> Optional[Contact]:
        """Get a single contact by ID."""
        query = select(Contact).where(Contact.id == contact_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(
        session: AsyncSession,
        data: ContactCreate,
        user_id: Optional[int] = None,
    ) -> Contact:
        """
        Create a new contact.
        
        Args:
            session: Database session
            data: Contact creation data
            user_id: Optional ID of user creating this contact
            
        Returns:
            The created Contact object
        """
        contact = Contact(
            name=data.name,
            email=data.email,
            phone=data.phone,
            discord_id=data.discord_id,
            discord_username=data.discord_username,
            notes=data.notes,
            tags=data.tags,
            created_by=user_id,
        )
        
        session.add(contact)
        await session.commit()
        await session.refresh(contact)
        
        # Log the action
        log = ActivityLog(
            user_id=user_id,
            action="create_contact",
            details={"contact_id": contact.id, "contact_name": contact.name},
            status="success",
        )
        session.add(log)
        await session.commit()
        
        return contact
    
    @staticmethod
    async def update(
        session: AsyncSession,
        contact_id: int,
        data: ContactUpdate,
    ) -> Optional[Contact]:
        """
        Update an existing contact.
        
        Only updates fields that are provided (not None).
        """
        contact = await ContactService.get_by_id(session, contact_id)
        if not contact:
            return None
        
        # Update only provided fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contact, field, value)
        
        contact.updated_at = datetime.now(timezone.utc)
        
        await session.commit()
        await session.refresh(contact)
        
        return contact
    
    @staticmethod
    async def delete(
        session: AsyncSession,
        contact_id: int,
        user_id: Optional[int] = None,
    ) -> bool:
        """
        Delete a contact by ID.
        
        Returns True if deleted, False if not found.
        """
        contact = await ContactService.get_by_id(session, contact_id)
        if not contact:
            return False
        
        contact_name = contact.name
        await session.delete(contact)
        await session.commit()
        
        # Log the action
        log = ActivityLog(
            user_id=user_id,
            action="delete_contact",
            details={"contact_id": contact_id, "contact_name": contact_name},
            status="success",
        )
        session.add(log)
        await session.commit()
        
        return True
    
    @staticmethod
    async def search(
        session: AsyncSession,
        query: str,
        limit: int = 20,
    ) -> List[Contact]:
        """
        Search contacts by name, email, or Discord username.
        
        Uses case-insensitive ILIKE for PostgreSQL.
        """
        search_pattern = f"%{query}%"
        stmt = (
            select(Contact)
            .where(
                (Contact.name.ilike(search_pattern)) |
                (Contact.email.ilike(search_pattern)) |
                (Contact.discord_username.ilike(search_pattern))
            )
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
