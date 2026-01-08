from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, Text, Integer, DateTime
from sqlalchemy.sql import func
from typing import Optional, List
from datetime import datetime
from .base import Base, TimestampMixin

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    role: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    discord_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    @property
    def is_admin(self) -> bool:
        return self.role == 0

    api_keys: Mapped[List["APIKey"]] = relationship("APIKey", back_populates="owner")
    google_tokens: Mapped[List["GoogleToken"]] = relationship("GoogleToken", back_populates="user")
