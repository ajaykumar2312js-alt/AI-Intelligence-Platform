from fastapi import APIRouter, Depends

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.api.deps import get_chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat_with_documents(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
):
    result = await service.chat(
        query=request.query,
        document_ids=request.document_ids,
        top_k=request.top_k,
    )
    return ChatResponse(answer=result["answer"], citations=result["citations"])
