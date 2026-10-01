from uuid import UUID

from app.embeddings.sentence_transformer import embed_query
from app.repositories.document_repository import DocumentRepository
from app.repositories.chunk_repository import ChunkRepository


class SearchService:
    def __init__(self, doc_repo: DocumentRepository, chunk_repo: ChunkRepository):
        self.doc_repo = doc_repo
        self.chunk_repo = chunk_repo

    async def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        document_ids: list[UUID] | None = None,
    ) -> list[dict]:
        query_embedding = embed_query(query)

        chunks = await self.chunk_repo.search(
            query_embedding, top_k=top_k, document_ids=document_ids
        )

        results = []
        for chunk in chunks:
            doc_id = chunk["document_id"]
            doc = await self.doc_repo.get_by_id(doc_id)
            filename = doc["filename"] if doc else None

            results.append({
                "chunk_id": chunk["id"],
                "document_id": doc_id,
                "content": chunk["content"],
                "score": float(chunk["score"]),
                "filename": filename,
                "chunk_index": chunk["chunk_index"],
            })

        return results
