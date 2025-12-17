from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from src.core.database import get_db
from src.core.security import get_current_user
from src.services.ai.chat_service import UnifiedChatService

router = APIRouter()
chat_service = UnifiedChatService()

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str

@router.post("/query", response_model=ChatResponse)
async def query_platform(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Unified Voice Assistant Endpoint.
    Propagates query to ChatService which aggregates data from across the platform.
    """
    try:
        answer = await chat_service.answer_query(request.query, db)
        return ChatResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
