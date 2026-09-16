import uuid
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings

_client: chromadb.ClientAPI | None = None
_collection: chromadb.Collection | None = None

COLLECTION_NAME = "rag_documents"


def _get_collection() -> chromadb.Collection:
    global _client, _collection
    if _collection is not None:
        return _collection

    _client = chromadb.Client(ChromaSettings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=settings.CHROMA_PERSIST_DIR,
        anonymized_telemetry=False,
    ))

    _collection = _client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    return _collection


def upsert_vectors(vectors: list[dict]) -> None:
    collection = _get_collection()
    ids = [v["id"] for v in vectors]
    embeddings = [v["values"] for v in vectors]
    metadatas = [v.get("metadata", {}) for v in vectors]
    documents = [v.get("metadata", {}).get("content", "") for v in vectors]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        metadatas=metadatas,
        documents=documents,
    )


def query_vectors(
    vector: list[float],
    top_k: int = 5,
    filter_dict: dict | None = None,
) -> list[dict]:
    collection = _get_collection()

    where = None
    if filter_dict:
        where = _convert_filter(filter_dict)

    results = collection.query(
        query_embeddings=[vector],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    matches = []
    if results and results["ids"]:
        for i, doc_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i] if results["distances"] else 0.0
            score = 1.0 - distance
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            matches.append({
                "id": doc_id,
                "score": score,
                "metadata": meta,
            })

    return matches


def delete_vectors(ids: list[str]) -> None:
    collection = _get_collection()
    collection.delete(ids=ids)


def delete_by_filter(filter_dict: dict) -> None:
    collection = _get_collection()
    where = _convert_filter(filter_dict)
    collection.delete(where=where)


def generate_id() -> str:
    return str(uuid.uuid4())


def _convert_filter(filter_dict: dict) -> dict:
    """Convert filter dict to ChromaDB where clause."""
    if "$in" in filter_dict.get("document_id", {}):
        doc_ids = filter_dict["document_id"]["$in"]
        return {"document_id": {"$in": doc_ids}}

    converted = {}
    for key, value in filter_dict.items():
        if isinstance(value, dict):
            if "$in" in value:
                converted[key] = {"$in": value["$in"]}
            elif "$eq" in value:
                converted[key] = {"$eq": value["$eq"]}
            else:
                converted[key] = value
        else:
            converted[key] = {"$eq": value}

    return converted
