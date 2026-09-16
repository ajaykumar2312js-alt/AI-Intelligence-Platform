from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID


@dataclass
class Chunk:
    id: UUID
    document_id: UUID
    content: str
    chunk_index: int
    vector_id: str
    token_count: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
