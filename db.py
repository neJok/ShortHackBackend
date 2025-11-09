from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


MONGO_DB_TOKEN = os.getenv('MONGO_DB_TOKEN')
client = AsyncIOMotorClient()
db = client["events_db"]
collection = db["events"]


class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    image: Optional[str] = None
    max_users: int
    started_at: datetime
    until_at: datetime


def create_event(event: EventCreate):
    # Превращаем в dict и сохраняем
    event_dict = event.dict()
    result = collection.insert_one(event_dict)
