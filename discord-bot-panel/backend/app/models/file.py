from sqlalchemy import Integer, String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin


class FileRecord(Base, TimestampMixin):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    local_path: Mapped[str] = mapped_column(String, nullable=False)
