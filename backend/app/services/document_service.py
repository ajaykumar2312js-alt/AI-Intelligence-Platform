import os
import uuid
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile

from app.repositories.document_repository import DocumentRepository
from app.repositories.chunk_repository import ChunkRepository
from app.workers.document_tasks import process_document

UPLOAD_DIR = Path("uploads")


class DocumentService:
    def __init__(
        self,
        doc_repo: DocumentRepository,
        chunk_repo: ChunkRepository,
    ):
        self.doc_repo = doc_repo
        self.chunk_repo = chunk_repo

    async def upload_document(self, file: UploadFile) -> dict:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        file_ext = Path(file.filename or "unknown").suffix
        saved_name = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / saved_name

        content = await file.read()
        file_path.write_bytes(content)

        doc = await self.doc_repo.create(
            filename=file.filename or saved_name,
            content_type=file.content_type or "application/octet-stream",
        )

        process_document.delay(str(doc["id"]), str(file_path))

        return doc

    async def get_document(self, doc_id: UUID) -> dict | None:
        return await self.doc_repo.get_by_id(doc_id)

    async def list_documents(self, offset: int = 0, limit: int = 20) -> dict:
        docs = await self.doc_repo.list_documents(offset, limit)
        total = await self.doc_repo.count()
        return {"documents": docs, "total": total, "offset": offset, "limit": limit}

    async def delete_document(self, doc_id: UUID) -> bool:
        from app.vector_store.chroma_store import delete_vectors

        chunks = await self.chunk_repo.get_by_document(doc_id)
        if chunks:
            vector_ids = [c["vector_id"] for c in chunks]
            delete_vectors(vector_ids)

        await self.chunk_repo.delete_by_document(doc_id)
        deleted = await self.doc_repo.delete(doc_id)

        return deleted
