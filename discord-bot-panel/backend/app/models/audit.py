from datetime import datetime
from sqlalchemy import Integer, String, Text, ForeignKey, JSON, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional, Any
from .base import Base

class AuditLog(Base):
    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="success")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
