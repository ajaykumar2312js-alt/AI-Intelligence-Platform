from pydantic import BaseModel, Field
from uuid import UUID


class Citation(BaseModel):
    chunk_id: UUID
    document_id: UUID
    content: str
    filename: str | None = None
    chunk_index: int


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User question")
    document_ids: list[UUID] | None = Field(
        default=None, description="Limit to specific documents"
    )
    top_k: int = Field(default=5, ge=1, le=20)


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
