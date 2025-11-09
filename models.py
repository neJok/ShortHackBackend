from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from fastapi import Form
from fastapi.security import OAuth2PasswordRequestForm
from enum import Enum



class EventType(Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"


# class OAuth2EmailRequestForm(OAuth2PasswordRequestForm):
#     def __init__(
#         self,
#         email: str = Form(...),
#         password: str = Form(...),
#         scope: str = Form(""),
#         client_id: str | None = Form(None),
#         client_secret: str | None = Form(None),
#     ):
#         super().__init__(
#             username=email,
#             password=password,
#             scope=scope,
#             client_id=client_id,
#             client_secret=client_secret,
#         )


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
    tower: str
    equipment: List[str] = []

class Event(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    image_url: Optional[str] = None
    event_type: EventType
    location: Optional[dict] = None


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
    image_url: str | None = None
    event_type: EventType
    location: dict | None = None

    @validator("location", always=True)
    def validate_location(cls, v, values):
        event_type = values.get("event_type")
        if event_type == EventType.ONLINE:
            if v is not None:
                raise ValueError("Location must not be provided for an ONLINE event.")
        elif event_type == EventType.OFFLINE:
            if v is None:
                raise ValueError("Location is required for an OFFLINE event.")

            if "type" not in v or v["type"] not in ["dukat", "custom"]:
                raise ValueError("Location type must be 'dukat' or 'custom'.")

            if v["type"] == "dukat":
                tower = v.get("tower")
                room_number = v.get("room_number")
                if tower not in ["F", "B"] or not room_number:
                    raise ValueError("Invalid Dukat location details.")
                if not is_valid_dukat_room(tower, room_number):
                    raise ValueError("Invalid room.")
            elif v["type"] == "custom":
                if not v.get("address"):
                    raise ValueError("Address is required for a custom location.")
        return v

class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"