from uuid import UUID

from openai import AsyncOpenAI

from app.core.config import settings
from app.embeddings.sentence_transformer import embed_query
from app.repositories.document_repository import DocumentRepository
from app.repositories.chunk_repository import ChunkRepository


SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions based on the provided context. "
    "Always cite your sources by referencing the Source number. "
    "If the answer is not in the context, say so clearly."
)


class ChatService:
    def __init__(self, doc_repo: DocumentRepository, chunk_repo: ChunkRepository):
        self.doc_repo = doc_repo
        self.chunk_repo = chunk_repo

    async def chat(
        self,
        query: str,
        document_ids: list[UUID] | None = None,
        top_k: int = 5,
    ) -> dict:
        context_chunks = await self._retrieve_context(query, top_k, document_ids)

        user_message = self._build_prompt(query, context_chunks)

        answer = await self._call_nvidia(user_message)

        citations = []
        for chunk in context_chunks:
            doc_id = chunk["document_id"]
            doc = await self.doc_repo.get_by_id(doc_id)
            filename = doc["filename"] if doc else None

            citations.append({
                "chunk_id": chunk["id"],
                "document_id": doc_id,
                "content": chunk["content"],
                "filename": filename,
                "chunk_index": chunk["chunk_index"],
            })

        return {"answer": answer, "citations": citations}

    async def _retrieve_context(
        self,
        query: str,
        top_k: int,
        document_ids: list[UUID] | None,
    ) -> list[dict]:
        query_embedding = embed_query(query)
        return await self.chunk_repo.search(
            query_embedding, top_k=top_k, document_ids=document_ids
        )

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
            f"## Context\n\n{context}\n\n"
            f"## Question\n\n{query}\n\n"
            "## Answer\n"
        )

    async def _call_nvidia(self, user_message: str) -> str:
        if not settings.NVIDIA_API_KEY:
            raise RuntimeError(
                "NVIDIA_API_KEY is not set. Add it to your .env file "
                "(get one at https://build.nvidia.com)."
            )

        client = AsyncOpenAI(
            base_url=settings.NVIDIA_BASE_URL,
            api_key=settings.NVIDIA_API_KEY,
            timeout=120.0,
        )

        response = await client.chat.completions.create(
            model=settings.NVIDIA_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
        )

        return response.choices[0].message.content or ""
