from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class User(BaseModel):
    id: int
    full_name: str
    username: Optional[str]
    phone: Optional[str]
    balance: int = 0
    registered_at: datetime

class Project(BaseModel):
    id: int
    title: str
    link: str
    is_active: bool = False
    created_at: datetime

class Vote(BaseModel):
    id: int
    user_id: int
    project_id: int
    photo_id: str
    phone: str
    card_number: Optional[str]
    is_confirmed: bool = False
    created_at: datetime