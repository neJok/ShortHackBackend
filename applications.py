from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
from bson import ObjectId

from db import db, collection
from models import EventApplication, User
from security import role_checker
from bot import send_notif
router = APIRouter()


class ModerationRequest(BaseModel):
    status: str
    assigned_room_id: Optional[str] = None
    curator_comment: Optional[str] = None


@router.post("/", response_model=EventApplication, status_code=status.HTTP_201_CREATED)
async def create_application(
    application_data: ApplicationCreate,
    current_user: User = Depends(role_checker(["student"])),
):
    application = EventApplication(**application_data.model_dump())
    application.organizer_id = current_user.id
    application.status = "pending"
    application.assigned_room_id = None # Explicitly set room_id to None on creation

    new_application = await db.applications.insert_one(
        application.model_dump(by_alias=True, exclude=["id"])
    )
    created_application = await db.applications.find_one(
        {"_id": new_application.inserted_id}
    )
    return created_application


@router.get("/", response_model=List[EventApplication])
async def get_applications(
    current_user: User = Depends(role_checker(["student", "curator", "admin"])),
):
    if current_user.role == "student":
        applications = await db.applications.find({"organizer_id": current_user.id}).to_list(1000)
        return applications

    applications = await db.applications.find().to_list(1000)
    return applications


@router.get("/{id}", response_model=EventApplication)
async def get_application(
    id: str,
    current_user: User = Depends(role_checker(["student", "curator", "admin"])),
):
    application = await db.applications.find_one({"_id": ObjectId(id)})
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")

    if current_user.role == "student" and application["organizer_id"] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Не авторизован для доступа к этой заявке")

    return application


@router.patch("/{id}/moderate", response_model=EventApplication)
async def moderate_application(
    id: str,
    moderation: ModerationRequest,
    current_user: User = Depends(role_checker(["curator"])),
):
    application = await db.applications.find_one({"_id": ObjectId(id)})
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")

    if moderation.status == "approved":
        if not moderation.assigned_room_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Идентификатор назначенной комнаты обязателен для подтверждения")

        # Check for room availability
        conflicting_applications = await db.applications.find({
            "assigned_room_id": moderation.assigned_room_id,
            "status": "approved",
            "_id": {"$ne": ObjectId(id)},
            "start_time": {"$lt": application["end_time"]},
            "end_time": {"$gt": application["start_time"]},
        }).to_list(1)

        if conflicting_applications:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Комната уже забронирована на это время")

    update_data = {
        "status": moderation.status,
        "assigned_room_id": moderation.assigned_room_id,
        "curator_comment": moderation.curator_comment,
    }
    await db.applications.update_one({"_id": ObjectId(id)}, {"$set": update_data})
    ststus_changed_user_tg = collection.find_one("user_tg_id")
    if ststus_changed_user_tg:
        await send_notif(status, ststus_changed_user_tg)
    updated_application = await db.applications.find_one({"_id": ObjectId(id)})
    return updated_application