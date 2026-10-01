import asyncio
import logging
from pathlib import Path
from uuid import UUID

from app.workers.celery_app import celery_app
from app.core.config import settings
from app.processors.extractor import extract_content
from app.processors.chunker import chunk_text
from app.embeddings.sentence_transformer import embed_texts

logger = logging.getLogger(__name__)


@celery_app.task(name="process_document", bind=True, max_retries=3)
def process_document(self, document_id: str, file_path: str):
    asyncio.run(_process_document_async(document_id, file_path))


async def _process_document_async(document_id: str, file_path: str):
    import asyncpg

    dsn = settings.DATABASE_URL.replace("+asyncpg", "")
    ssl = "require" if "localhost" not in dsn and "127.0.0.1" not in dsn else None
    pool = await asyncpg.create_pool(dsn, min_size=1, max_size=2, ssl=ssl)

    try:
        await pool.execute(
            "UPDATE documents SET status = 'processing', updated_at = NOW() WHERE id = $1",
            UUID(document_id),
        )

        content_type = _guess_content_type(file_path)
        text = await extract_content(Path(file_path), content_type)

        if not text.strip():
            await pool.execute(
                "UPDATE documents SET status = 'failed', updated_at = NOW() WHERE id = $1",
                UUID(document_id),
            )
            logger.warning("Document %s: extracted empty content", document_id)
            return

        chunks = chunk_text(text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)

        chunk_contents = [c.content for c in chunks]
        embeddings = embed_texts(chunk_contents)

        chunk_records = [
            {
                "document_id": document_id,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
                "embedding": embedding,
            }
            for chunk, embedding in zip(chunks, embeddings)
        ]

        if chunk_records:
            contents = [c["content"] for c in chunk_records]
            indices = [c["chunk_index"] for c in chunk_records]
            token_counts = [c["token_count"] for c in chunk_records]
            vector_literals = [
                "[" + ",".join(str(v) for v in c["embedding"]) + "]"
                for c in chunk_records
            ]
            await pool.fetch(
                """INSERT INTO chunks (document_id, content, chunk_index, token_count, embedding)
                   SELECT $1::uuid, unnest($2::text[]), unnest($3::int[]),
                          unnest($4::int[]), (unnest($5::text[]))::vector""",
                UUID(document_id), contents, indices, token_counts, vector_literals,
            )

        await pool.execute(
            """UPDATE documents
               SET status = 'completed', chunk_count = $1, updated_at = NOW()
               WHERE id = $2""",
            len(chunks), UUID(document_id),
        )

        logger.info("Document %s processed: %d chunks", document_id, len(chunks))

    except Exception as e:
        logger.error("Failed to process document %s: %s", document_id, e)
        await pool.execute(
            "UPDATE documents SET status = 'failed', updated_at = NOW() WHERE id = $1",
            UUID(document_id),
        )
        raise

    finally:
        await pool.close()


def _guess_content_type(file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()
    mapping = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".html": "text/html",
        ".htm": "text/html",
        ".csv": "text/csv",
    }
    return mapping.get(suffix, "application/octet-stream")
