from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

class User(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    full_name: str
    email: str
    hashed_password: str
    role: str = "student"  # student, curator, admin

class Room(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    name: str
    capacity: int

class EventApplication(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    organizer_id: str
    room_id: Optional[int] = None
    status: str = "pending"  # pending, approved, rejected
    assigned_room_id: Optional[int] = None
    curator_comment: Optional[str] = None

class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"