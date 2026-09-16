from uuid import UUID

from app.embeddings.sentence_transformer import embed_query
from app.vector_store.chroma_store import query_vectors
from app.repositories.document_repository import DocumentRepository


class SearchService:
    def __init__(self, doc_repo: DocumentRepository):
        self.doc_repo = doc_repo

    async def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        document_ids: list[UUID] | None = None,
    ) -> list[dict]:
        query_embedding = embed_query(query)

        filter_dict = None
        if document_ids:
            filter_dict = {
                "document_id": {"$in": [str(did) for did in document_ids]}
            }

        matches = query_vectors(query_embedding, top_k=top_k, filter_dict=filter_dict)

        results = []
        for match in matches:
            meta = match.get("metadata", {})
            doc_id = meta.get("document_id")
            filename = None
            if doc_id:
                doc = await self.doc_repo.get_by_id(UUID(doc_id))
                if doc:
                    filename = doc["filename"]

            results.append({
                "chunk_id": meta.get("chunk_id"),
                "document_id": doc_id,
                "content": meta.get("content", ""),
                "score": match.get("score", 0.0),
                "filename": filename,
                "chunk_index": meta.get("chunk_index", 0),
            })

        return results
