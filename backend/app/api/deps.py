from app.core.database import get_pool
from app.repositories.document_repository import DocumentRepository
from app.repositories.chunk_repository import ChunkRepository
from app.services.document_service import DocumentService
from app.services.search_service import SearchService
from app.services.chat_service import ChatService


def get_document_repo() -> DocumentRepository:
    return DocumentRepository(get_pool())


def get_chunk_repo() -> ChunkRepository:
    return ChunkRepository(get_pool())


def get_document_service() -> DocumentService:
    return DocumentService(get_document_repo(), get_chunk_repo())


def get_search_service() -> SearchService:
    return SearchService(get_document_repo(), get_chunk_repo())


def get_chat_service() -> ChatService:
    return ChatService(get_document_repo(), get_chunk_repo())
