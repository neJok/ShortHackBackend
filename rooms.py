from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import date, datetime, time
from db import db
from models import Room
from security import get_current_user
from auth import get_user_from_db

router = APIRouter()

@router.get("/rooms", response_model=List[Room])
async def get_rooms(current_user: dict = Depends(get_current_user)):
    """
    Get a list of all rooms.
    Accessible to authenticated users (student, curator).
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await get_user_from_db(current_user["email"])
    if user["role"] not in ["student", "curator"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    rooms = await db.rooms.find().to_list(1000)
    return rooms

@router.get("/rooms/{id}/availability")
async def get_room_availability(id: str, date: date, current_user: dict = Depends(get_current_user)):
    """
    Get the availability of a room for a specific date.
    Returns a list of booked time slots.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = await get_user_from_db(current_user["email"])
    if user["role"] not in ["student", "curator"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    room = await db.rooms.find_one({"_id": id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    start_of_day = datetime.combine(date, time.min)
    end_of_day = datetime.combine(date, time.max)

    applications = await db.event_applications.find({
        "room_id": id,
        "status": "approved",
        "start_time": {"$gte": start_of_day, "$lt": end_of_day}
    }).to_list(1000)

    booked_slots = []
    for app in applications:
        booked_slots.append({
            "start_time": app["start_time"].time(),
            "end_time": app["end_time"].time()
        })

    return {"date": date, "booked_slots": booked_slots}
