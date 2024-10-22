from fastapi import APIRouter, Depends
from app.models.schemas import ChatMessage, ChatResponse
from app.services.ai_service import AIService

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat(message: ChatMessage, ai_service: AIService = Depends()):
    response = await ai_service.generate_response(message.content)
    return ChatResponse(response=response)