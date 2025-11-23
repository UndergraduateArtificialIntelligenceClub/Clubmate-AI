from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class ROLES:
    pleb = 1
    admin = 0


class FibInput(BaseModel):
    n: int


class TextInput(BaseModel):
    t: str
