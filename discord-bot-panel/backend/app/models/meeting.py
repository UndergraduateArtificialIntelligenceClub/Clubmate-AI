from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organizer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(1024), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meeting_link: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attendees: Mapped[List[str]] = mapped_column(JSON, default=[], nullable=True) # JSONB in DB
    google_calendar_event_id: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="scheduled")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    organizer: Mapped["User"] = relationship("User")
