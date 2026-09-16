import asyncpg
import json
from uuid import UUID


class DocumentRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create(self, filename: str, content_type: str, metadata: dict | None = None) -> dict:
        meta_json = json.dumps(metadata) if metadata else None
        row = await self.pool.fetchrow(
            """INSERT INTO documents (filename, content_type, metadata)
               VALUES ($1, $2, $3::jsonb) RETURNING *""",
            filename, content_type, meta_json,
        )
        return dict(row)

    async def get_by_id(self, doc_id: UUID) -> dict | None:
        row = await self.pool.fetchrow(
            "SELECT * FROM documents WHERE id = $1", doc_id
        )
        return dict(row) if row else None

    async def update_status(self, doc_id: UUID, status: str, chunk_count: int | None = None):
        if chunk_count is not None:
            await self.pool.execute(
                """UPDATE documents
                   SET status = $1, chunk_count = $2, updated_at = NOW()
                   WHERE id = $3""",
                status, chunk_count, doc_id,
            )
        else:
            await self.pool.execute(
                "UPDATE documents SET status = $1, updated_at = NOW() WHERE id = $2",
                status, doc_id,
            )

    async def list_documents(self, offset: int = 0, limit: int = 20) -> list[dict]:
        rows = await self.pool.fetch(
            "SELECT * FROM documents ORDER BY created_at DESC OFFSET $1 LIMIT $2",
            offset, limit,
        )
        return [dict(r) for r in rows]

    async def count(self) -> int:
        row = await self.pool.fetchrow("SELECT COUNT(*) AS total FROM documents")
        return row["total"]

    async def delete(self, doc_id: UUID) -> bool:
        result = await self.pool.execute(
            "DELETE FROM documents WHERE id = $1", doc_id
        )
        return result == "DELETE 1"
