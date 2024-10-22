from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chat, rooms, bookings
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(rooms.router, prefix="/api/rooms", tags=["rooms"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["bookings"])

@app.get("/")
async def root():
    return {"message": "Welcome to AI Resorts Assistant API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)