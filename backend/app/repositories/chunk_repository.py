import asyncpg
from uuid import UUID


def _to_vector_literal(embedding: list[float]) -> str:
    """Convert a Python list of floats to a pgvector text literal."""
    return "[" + ",".join(str(v) for v in embedding) + "]"


class ChunkRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create_many(self, chunks: list[dict]) -> list[dict]:
        """Bulk insert chunks. Each dict must contain:
        document_id, content, chunk_index, token_count, embedding (list[float]).
        """
        if not chunks:
            return []
        doc_id = chunks[0]["document_id"]
        contents = [c["content"] for c in chunks]
        indices = [c["chunk_index"] for c in chunks]
        token_counts = [c["token_count"] for c in chunks]
        embeddings = [_to_vector_literal(c["embedding"]) for c in chunks]

        records = await self.pool.fetch(
            """INSERT INTO chunks (document_id, content, chunk_index, token_count, embedding)
               SELECT $1::uuid, unnest($2::text[]), unnest($3::int[]),
                      unnest($4::int[]), (unnest($5::text[]))::vector
               RETURNING *""",
            doc_id, contents, indices, token_counts, embeddings,
        )
        return [dict(r) for r in records]

    async def search(
        self,
        embedding: list[float],
        top_k: int = 5,
        document_ids: list[UUID] | None = None,
    ) -> list[dict]:
        """Cosine similarity search over chunk embeddings."""
        query_vector = _to_vector_literal(embedding)

        if document_ids:
            rows = await self.pool.fetch(
                """SELECT id, document_id, content, chunk_index, token_count,
                          1 - (embedding <=> $1::vector) AS score
                   FROM chunks
                   WHERE document_id = ANY($2::uuid[])
                   ORDER BY embedding <=> $1::vector
                   LIMIT $3""",
                query_vector, document_ids, top_k,
            )
        else:
            rows = await self.pool.fetch(
                """SELECT id, document_id, content, chunk_index, token_count,
                          1 - (embedding <=> $1::vector) AS score
                   FROM chunks
                   ORDER BY embedding <=> $1::vector
                   LIMIT $2""",
                query_vector, top_k,
            )

        return [dict(r) for r in rows]

    async def get_by_document(self, doc_id: UUID) -> list[dict]:
        rows = await self.pool.fetch(
            "SELECT * FROM chunks WHERE document_id = $1 ORDER BY chunk_index",
            doc_id,
        )
        return [dict(r) for r in rows]

    async def get_by_ids(self, chunk_ids: list[UUID]) -> list[dict]:
        rows = await self.pool.fetch(
            "SELECT * FROM chunks WHERE id = ANY($1::uuid[])",
            chunk_ids,
        )
        return [dict(r) for r in rows]

    async def delete_by_document(self, doc_id: UUID):
        await self.pool.execute(
            "DELETE FROM chunks WHERE document_id = $1", doc_id
        )
