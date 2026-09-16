import asyncpg
from uuid import UUID


class ChunkRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create_many(self, chunks: list[dict]) -> list[dict]:
        if not chunks:
            return []
        doc_id = chunks[0]["document_id"]
        contents = [c["content"] for c in chunks]
        indices = [c["chunk_index"] for c in chunks]
        vector_ids = [c["vector_id"] for c in chunks]
        token_counts = [c["token_count"] for c in chunks]

        records = await self.pool.fetch(
            """INSERT INTO chunks (document_id, content, chunk_index, vector_id, token_count)
               SELECT $1::uuid, unnest($2::text[]), unnest($3::int[]),
                      unnest($4::text[]), unnest($5::int[])
               RETURNING *""",
            doc_id, contents, indices, vector_ids, token_counts,
        )
        return [dict(r) for r in records]

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
