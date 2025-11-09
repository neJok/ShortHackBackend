from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class User(BaseModel):
    id: Optional[int] = None
    full_name: str
    email: str
    hashed_password: str
    role: str = "student"  # student, curator, admin

class Room(BaseModel):
    id: int
    name: str
    capacity: int

class EventApplication(BaseModel):
    id: int
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    organizer_id: int
    room_id: int
    status: str = "pending" # pending, approved, rejected

class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"