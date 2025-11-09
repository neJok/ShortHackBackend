import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel, validator
from datetime import datetime
from models import EventType

from db import db, collection
from models import EventApplication, User
from security import role_checker
from bot import send_notif
router = APIRouter()


class ModerationRequest(BaseModel):
    status: str
    assigned_room_id: Optional[str] = None
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
                raise ValueError("Местоположение не должно быть указано для ОНЛАЙН мероприятия.")
        elif event_type == EventType.OFFLINE:
            if v is None:
                raise ValueError("Местоположение обязательно для ОФФЛАЙН мероприятия.")

            if "type" not in v or v["type"] not in ["dukat", "custom"]:
                raise ValueError("Тип местоположения должен быть 'dukat' или 'custom'.")

            if v["type"] == "dukat":
                tower = v.get("tower")
                room_number = v.get("room_number")
                if tower not in ["F", "B"] or not room_number:
                    raise ValueError("Неверные данные местоположения Dukat.")
            elif v["type"] == "custom":
                if not v.get("address"):
                    raise ValueError("Адрес обязателен для пользовательского местоположения.")
        return v


@router.post("/", response_model=EventApplication, status_code=status.HTTP_201_CREATED)
async def create_application(
    application_data: ApplicationCreate,
    current_user: User = Depends(role_checker(["student"])),
):
    data = application_data.model_dump()
    data['organizer_id'] = current_user.id
    data['organizer_name'] = current_user.full_name
    data['status'] = "pending"
    data['_id'] = str(uuid.uuid4())
    application = EventApplication(**data)

    await db.applications.insert_one(data)
    return application


@router.get("/pendings", response_model=List[EventApplication])
async def get_applications(
    current_user: User = Depends(role_checker(["student", "curator", "admin"])),
):
    if current_user.role == "student":
        applications = await db.applications.find({"organizer_id": current_user.id, "status": "pendings"}).to_list(None)
        return applications

    applications = await db.applications.find().to_list(None)
    return applications

@router.get("/pendings", response_model=List[EventApplication])
async def get_applications():
    return await db.applications.find({"status": "approved"}).to_list(None)


@router.get("/{id}", response_model=EventApplication)
async def get_application(
    id: str,
):
    application = await db.applications.find_one({"_id": id})
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")

    return application


@router.patch("/{id}/moderate", response_model=EventApplication)
async def moderate_application(
    id: str,
    moderation: ModerationRequest,
    current_user: User = Depends(role_checker(["curator"])),
):
    application = await db.applications.find_one({"_id": id})
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")

    if moderation.status == "approved":
        if not moderation.assigned_room_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Идентификатор назначенной комнаты обязателен для подтверждения")

        # Check for room availability
        conflicting_applications = await db.applications.find({
            "assigned_room_id": moderation.assigned_room_id,
            "status": "approved",
            "_id": {"$ne": id},
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
    await db.applications.update_one({"_id": id}, {"$set": update_data})
    ststus_changed_user_tg = collection.find_one("user_tg_id")
    if ststus_changed_user_tg:
        await send_notif(status, ststus_changed_user_tg)
    updated_application = await db.applications.find_one({"_id": id})
    return updated_application