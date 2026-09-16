from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    content_type: str
    status: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int
    offset: int
    limit: int
