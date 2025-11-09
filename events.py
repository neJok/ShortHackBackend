from fastapi import FastAPI, status
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from db import collection

app = FastAPI()


class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    image: Optional[str] = None  # позже можно сделать UploadFile
    max_users: int
    started_at: datetime
    until_at: datetime


@app.post("/applications")
def create_event(event: EventCreate, status_code=status.HTTP_201_CREATED):
    event_dict = event.dict()
    result = collection.insert_one(event_dict)
    return {
            "title": "Турнир по шахматам",
            "description": "Ежегодный осенний турнир для всех желающих.",
            "start_time": "2024-10-26T14:00:00Z",
            "end_time": "2024-10-26T18:00:00Z",
            "expected_participants": 30,
            "needs": "15 шахматных досок, проектор для таблицы."
            }
