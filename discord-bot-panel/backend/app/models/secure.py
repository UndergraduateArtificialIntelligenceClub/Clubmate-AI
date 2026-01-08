from sqlalchemy import Integer, String, LargeBinary, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from .base import Base, TimestampMixin


class APIKey(Base, TimestampMixin):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)

    # Encryption fields
    encrypted_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    tag: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    owner: Mapped["User"] = relationship(back_populates="api_keys")


class GoogleToken(Base, TimestampMixin):
    __tablename__ = "google_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=False
    )

    encrypted_refresh_token: Mapped[bytes] = mapped_column(LargeBinary)
    nonce: Mapped[bytes] = mapped_column(LargeBinary)
    tag: Mapped[bytes] = mapped_column(LargeBinary)

    user: Mapped["User"] = relationship(back_populates="google_tokens")
