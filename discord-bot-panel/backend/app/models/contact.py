from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from typing import List, Optional
from .base import Base, TimestampMixin


class Contact(Base, TimestampMixin):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, index=True)
    discord_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # JSONB requires a cast in asyncpg usually, but SQLAlchemy handles it well
    # if the driver supports it. If using SQLite, use JSON instead.
    roles: Mapped[List[str]] = mapped_column(JSONB, default=list)

    status: Mapped[str] = mapped_column(String, default="active")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
