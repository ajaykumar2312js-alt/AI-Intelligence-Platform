from pydantic import BaseModel, Field
from uuid import UUID


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results")
    document_ids: list[UUID] | None = Field(
        default=None, description="Filter by specific document IDs"
    )


class SearchResult(BaseModel):
    chunk_id: UUID
    document_id: UUID
    content: str
    score: float
    filename: str | None = None
    chunk_index: int


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
