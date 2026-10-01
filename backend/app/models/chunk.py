from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID


@dataclass
class Chunk:
    id: UUID
    document_id: UUID
    content: str
    chunk_index: int
    token_count: int
    embedding: list[float] | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
