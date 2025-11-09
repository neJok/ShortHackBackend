from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
from bson import ObjectId

from db import db
from models import EventApplication, User, ApplicationCreate
from security import role_checker

router = APIRouter()


class ModerationRequest(BaseModel):
    status: str
    assigned_room_id: Optional[int] = None
    curator_comment: Optional[str] = None


@router.post("/applications", response_model=EventApplication, status_code=status.HTTP_201_CREATED)
async def create_application(
    application_data: ApplicationCreate,
    current_user: User = Depends(role_checker(["student"])),
):
    application = EventApplication(
        **application_data.model_dump(),
        organizer_id=current_user.id,
        status="pending",
        room_id=None,
        assigned_room_id=None,
        curator_comment=None,
    )

    new_application = await db.applications.insert_one(
        application.model_dump(by_alias=True, exclude=["id"])
    )
    created_application = await db.applications.find_one(
        {"_id": new_application.inserted_id}
    )
    return created_application


@router.get("/applications", response_model=List[EventApplication])
async def get_applications(
    current_user: User = Depends(role_checker(["student", "curator", "admin"])),
):
    if current_user.role == "student":
        applications = await db.applications.find({"organizer_id": current_user.id}).to_list(1000)
        return applications

    applications = await db.applications.find().to_list(1000)
    return applications


@router.get("/applications/{id}", response_model=EventApplication)
async def get_application(
    id: str,
    current_user: User = Depends(role_checker(["student", "curator", "admin"])),
):
    application = await db.applications.find_one({"_id": ObjectId(id)})
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    if current_user.role == "student" and application["organizer_id"] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this application")

    return application


@router.patch("/applications/{id}/moderate", response_model=EventApplication)
async def moderate_application(
    id: str,
    moderation: ModerationRequest,
    current_user: User = Depends(role_checker(["curator"])),
):
    application = await db.applications.find_one({"_id": ObjectId(id)})
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    if moderation.status == "approved":
        if not moderation.assigned_room_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assigned room ID is required for approval")

        # Check for room availability
        conflicting_applications = await db.applications.find({
            "assigned_room_id": moderation.assigned_room_id,
            "status": "approved",
            "_id": {"$ne": ObjectId(id)},
            "start_time": {"$lt": application["end_time"]},
            "end_time": {"$gt": application["start_time"]},
        }).to_list(1)

        if conflicting_applications:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Room is already booked for this time")

    update_data = {
        "status": moderation.status,
        "assigned_room_id": moderation.assigned_room_id,
        "curator_comment": moderation.curator_comment,
    }
    await db.applications.update_one({"_id": ObjectId(id)}, {"$set": update_data})

    updated_application = await db.applications.find_one({"_id": ObjectId(id)})
    return updated_application
from datetime import datetime


@router.get("/events", response_model=List[EventApplication])
async def get_events(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    query = {"status": "approved"}
    if start_date:
        query["end_time"] = {"$gte": start_date}
    if end_date:
        query["start_time"] = {"$lte": end_date}

    events = await db.applications.find(query).to_list(1000)
    return events