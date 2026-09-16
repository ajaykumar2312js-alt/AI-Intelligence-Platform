from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID


@dataclass
class Document:
    id: UUID
    filename: str
    content_type: str
    status: str
    chunk_count: int = 0
    metadata: dict | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
