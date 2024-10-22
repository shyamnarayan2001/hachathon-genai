from pydantic import BaseModel
from typing import List
from datetime import date

class ChatMessage(BaseModel):
    content: str

class ChatResponse(BaseModel):
    response: str

class Room(BaseModel):
    id: int
    name: str
    price: float

class AvailabilityRequest(BaseModel):
    check_in: date
    check_out: date

class BookingRequest(BaseModel):
    room_id: int
    check_in: date
    check_out: date
    guest_name: str

class BookingResponse(BookingRequest):
    id: int