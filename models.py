from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from fastapi import Form
from fastapi.security import OAuth2PasswordRequestForm

class OAuth2EmailRequestForm(OAuth2PasswordRequestForm):
    def __init__(
        self,
        email: str = Form(...),
        password: str = Form(...),
        scope: str = Form(""),
        client_id: str | None = Form(None),
        client_secret: str | None = Form(None),
    ):
        super().__init__(
            username=email,
            password=password,
            scope=scope,
            client_id=client_id,
            client_secret=client_secret,
        )


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
    equipment: List[str] = []

class EventApplication(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    organizer_id: str
    expected_participants: int
    needs: str
    room_id: Optional[int] = None
    status: str = "pending"  # pending, approved, rejected
    assigned_room_id: Optional[int] = None
    curator_comment: Optional[str] = None


class ApplicationCreate(BaseModel):
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    expected_participants: int
    needs: str
class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"