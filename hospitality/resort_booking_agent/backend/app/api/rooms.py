from fastapi import APIRouter, Depends
from typing import List
from app.models.schemas import Room, AvailabilityRequest
from app.db.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/available", response_model=List[Room])
async def get_available_rooms(request: AvailabilityRequest, db: Session = Depends(get_db)):
    # Implement logic to fetch available rooms from the database
    # This is a placeholder implementation
    available_rooms = [
        Room(id=1, name="Deluxe Room", price=200),
        Room(id=2, name="Suite", price=300),
    ]
    return available_rooms