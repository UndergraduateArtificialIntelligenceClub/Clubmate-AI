from pydantic import BaseModel
from typing import Optional

class ROLES:
    pleb = 1
    admin = 0

class FibInput(BaseModel):
    n: int

class TextInput(BaseModel):
    n: str

class User(BaseModel):
    role: int = ROLES.pleb # changable on initialization, and promotable if they for example become an exec
    discord_id: str # idk if we are converting the ids to ints or not
    email: Optional[str] # university email e.g. @ualberta.ca
    name: Optional[str]

    # def __init__(self, discord_id):
    #     # call database to determine role - in the exec UI, good to add role control there
    #     role_on_db = 
    #     if 
    #
