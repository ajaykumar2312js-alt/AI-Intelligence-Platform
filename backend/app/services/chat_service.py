import httpx
from uuid import UUID

from app.core.config import settings
from app.embeddings.sentence_transformer import embed_query
from app.vector_store.chroma_store import query_vectors
from app.repositories.document_repository import DocumentRepository


class ChatService:
    def __init__(self, doc_repo: DocumentRepository):
        self.doc_repo = doc_repo

    async def chat(
        self,
        query: str,
        document_ids: list[UUID] | None = None,
        top_k: int = 5,
    ) -> dict:
        context_chunks = await self._retrieve_context(query, top_k, document_ids)

        prompt = self._build_prompt(query, context_chunks)

        answer = await self._call_ollama(prompt)

        citations = []
        for chunk in context_chunks:
            doc_id = chunk.get("document_id")
            filename = None
            if doc_id:
                doc = await self.doc_repo.get_by_id(UUID(doc_id))
                if doc:
                    filename = doc["filename"]

            citations.append({
                "chunk_id": chunk.get("chunk_id"),
                "document_id": doc_id,
                "content": chunk.get("content", ""),
                "filename": filename,
                "chunk_index": chunk.get("chunk_index", 0),
            })

        return {"answer": answer, "citations": citations}

    async def _retrieve_context(
        self,
        query: str,
        top_k: int,
        document_ids: list[UUID] | None,
    ) -> list[dict]:
        query_embedding = embed_query(query)

        filter_dict = None
        if document_ids:
            filter_dict = {
                "document_id": {"$in": [str(did) for did in document_ids]}
            }

        matches = query_vectors(query_embedding, top_k=top_k, filter_dict=filter_dict)

        chunks = []
        for match in matches:
            meta = match.get("metadata", {})
            chunks.append({
                "chunk_id": meta.get("chunk_id"),
                "document_id": meta.get("document_id"),
                "content": meta.get("content", ""),
                "chunk_index": meta.get("chunk_index", 0),
                "score": match.get("score", 0.0),
            })

        return chunks

    def _build_prompt(self, query: str, context_chunks: list[dict]) -> str:
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            doc_id = chunk.get("document_id", "unknown")
            context_parts.append(
                f"[Source {i} | Document: {doc_id} | Chunk {chunk.get('chunk_index', 0)}]\n"
                f"{chunk['content']}"
            )

        context = "\n\n---\n\n".join(context_parts)

        return (
            "You are a helpful assistant that answers questions based on the provided context. "
            "Always cite your sources by referencing the Source number. "
            "If the answer is not in the context, say so clearly.\n\n"
            f"## Context\n\n{context}\n\n"
            f"## Question\n\n{query}\n\n"
            "## Answer\n"
        )

    async def _call_ollama(self, prompt: str) -> str:
        url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
