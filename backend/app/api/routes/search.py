from fastapi import APIRouter, Depends

from app.schemas.search import SearchRequest, SearchResponse, SearchResult
from app.services.search_service import SearchService
from app.api.deps import get_search_service

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    service: SearchService = Depends(get_search_service),
):
    results = await service.semantic_search(
        query=request.query,
        top_k=request.top_k,
        document_ids=request.document_ids,
    )
    return SearchResponse(query=request.query, results=results)
