from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import date, datetime, time
from db import db
from models import Room
from security import get_current_user
from auth import get_user_from_db

router = APIRouter()

@router.get("/", response_model=List[Room])
async def get_available_rooms(
    tower: str,
    start_time: datetime,
    end_time: datetime,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a list of available rooms based on specified criteria.
    Accessible to authenticated users (student, curator).
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = await get_user_from_db(current_user["email"])
    if user["role"] not in ["student", "curator"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    # Implementation for availability logic will go here
    available_rooms = []
    all_rooms_in_tower = await db.rooms.find({"tower": tower}).to_list(1000)

    for room_data in all_rooms_in_tower:
        room = Room(**room_data)
        
        # Check for conflicting applications
        conflicting_applications = await db.event_applications.find({
            "assigned_room_id": room.id,
            "status": "approved",
            "$or": [
                {
                    "start_time": {"$lt": end_time},
                    "end_time": {"$gt": start_time}
                },
                {
                    "start_time": {"$gte": start_time, "$lt": end_time}
                },
                {
                    "end_time": {"$gt": start_time, "$lte": end_time}
                }
            ]
        }).to_list(1) # We only need to know if there's *any* conflict

        if not conflicting_applications:
            available_rooms.append(room)
            
    return available_rooms

@router.get("/{id}/availability")
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
