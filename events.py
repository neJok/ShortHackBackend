from fastapi import APIRouter, Depends, status
from datetime import datetime
from typing import Optional
from db import db
from models import Event, User, ApplicationCreate, EventType
from pydantic import BaseModel, validator
from rooms import is_valid_dukat_room
from security import role_checker
class EventCreateRequest(BaseModel):
    name: str
    description: str
    start_time: datetime
    end_time: datetime
    image_url: str | None = None
    event_type: EventType
    location: dict | None = None

    @validator('location', pre=True, always=True)
    def validate_location(cls, v, values):
        event_type = values.get('event_type')
        if event_type == EventType.ONLINE:
            if v is not None:
                raise ValueError("Location must not be provided for an ONLINE event.")
            return None
        elif event_type == EventType.OFFLINE:
            if v is None or not v:
                raise ValueError("Location is required for an OFFLINE event.")

            if "type" not in v or v["type"] not in ["dukat", "custom"]:
                raise ValueError("Location type must be 'dukat' or 'custom'.")

            if v["type"] == "dukat":
                tower = v.get("tower")
                room_number = v.get("room_number")
                if tower not in ["F", "B"] or not room_number:
                    raise ValueError("Dukat location must specify 'tower' ('F' or 'B') and 'room_number'.")
                if not is_valid_dukat_room(tower, room_number):
                    raise ValueError("Invalid Dukat room.")
            elif v["type"] == "custom":
                if not v.get("address"):
                    raise ValueError("Custom location must specify a non-empty 'address'.")
        return v

router = APIRouter()


@router.post("/events", response_model=Event, status_code=status.HTTP_201_CREATED)
async def create_event(
    event: EventCreateRequest,
    current_user: User = Depends(role_checker(["student", "curator", "admin"])),
):
    owner_id = current_user.id
    db_event = Event(
        name=event.name,
        description=event.description,
        start_time=event.start_time,
        end_time=event.end_time,
        owner_id=owner_id,
        image_url=event.image_url,
        event_type=event.event_type,
        location=event.location,
    )
    
    await db.events.insert_one(
        db_event.model_dump(by_alias=True, exclude=["id"])
    )
    
    return db_event
