import tiktoken
from dataclasses import dataclass


@dataclass
class ChunkData:
    content: str
    chunk_index: int
    token_count: int


def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 50,
) -> list[ChunkData]:
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)

    if len(tokens) <= chunk_size:
        return [
            ChunkData(content=text, chunk_index=0, token_count=len(tokens))
        ]

    chunks: list[ChunkData] = []
    start = 0
    index = 0

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text_decoded = enc.decode(chunk_tokens)

        chunks.append(
            ChunkData(
                content=chunk_text_decoded,
                chunk_index=index,
                token_count=len(chunk_tokens),
            )
        )

        start += chunk_size - overlap
        index += 1

    return chunks
