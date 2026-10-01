import asyncpg
import os

from app.core.config import settings

pool: asyncpg.Pool | None = None


async def init_db() -> None:
    global pool
    dsn = settings.DATABASE_URL.replace("+asyncpg", "")
    ssl = "require" if "localhost" not in dsn and "127.0.0.1" not in dsn else None
    pool = await asyncpg.create_pool(dsn, min_size=2, max_size=10, ssl=ssl)

    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path) as f:
        schema = f.read()

    async with pool.acquire() as conn:
        await conn.execute(schema)


async def close_db() -> None:
    global pool
    if pool:
        await pool.close()
        pool = None


def get_pool() -> asyncpg.Pool:
    if pool is None:
        raise RuntimeError("Database pool not initialized. Call init_db() first.")
    return pool
