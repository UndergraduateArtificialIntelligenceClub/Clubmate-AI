from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class ROLES:
    pleb = 1
    admin = 0

class FibInput(BaseModel):
    n: int

class TextInput(BaseModel):
    t: str

class User(BaseModel):
    username: str
    role: int # Changable on initialization, and promotable if they for example become an exec
    discord_id: str # idk if we are converting the ids to ints or not (prolly not tbh, just checked discord api seems it is all strs)
    email: str # University email e.g. @ualberta.ca
    name: str

    created_at: datetime

    # def __init__(self, discord_id):
    #     # call database to determine role - in the exec UI, good to add role control there
    #     role_on_db = 
    #     if 
    #
