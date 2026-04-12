"""Qdrant 向量存储服务。"""

from __future__ import annotations

from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

from backend.app.config import settings
from backend.app.services.embedding_service import embed_query, embed_texts, get_embedding_model
from backend.app.services.sql_semantic_service import parse_sql_chunks

_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        if settings.qdrant_url:
            _client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)
        else:
            _client = QdrantClient(path=str(settings.qdrant_path))
    return _client


def ensure_collection(collection_name: str) -> None:
    client = get_qdrant_client()
    collections = [item.name for item in client.get_collections().collections]
    if collection_name in collections:
        return

    vector_size = len(embed_query("test query"))
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )


def build_collection_name(knowledge_base_id: str) -> str:
    return f"sql_kb_{knowledge_base_id.replace('-', '_')}"


def rebuild_sql_vectorstore(sql_texts: list[dict], knowledge_base_id: str):
    client = get_qdrant_client()
    collection_name = build_collection_name(knowledge_base_id)
    ensure_collection(collection_name)
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=len(embed_query("test query")), distance=Distance.COSINE),
    )

    all_chunks = []
    for item in sql_texts:
        file_name = item["source"]
        chunks = parse_sql_chunks(item["text"])
        for chunk in chunks:
            all_chunks.append({
                "source": file_name,
                "object_type": chunk.object_type,
                "object_name": chunk.object_name,
                "section": chunk.section,
                "summary": chunk.summary,
                "raw_text": chunk.raw_text,
                "retrieval_text": chunk.retrieval_text,
                "table_refs": chunk.table_refs,
                "action_types": chunk.action_types,
                "params": chunk.params,
            })

    vectors = embed_texts([item["retrieval_text"] for item in all_chunks]) if all_chunks else []
    points = []
    for item, vector in zip(all_chunks, vectors):
        points.append(
            PointStruct(
                id=str(uuid4()),
                vector=vector,
                payload={
                    "source": item["source"],
                    "object_type": item["object_type"],
                    "object_name": item["object_name"],
                    "section": item["section"],
                    "summary": item["summary"],
                    "raw_text": item["raw_text"],
                    "retrieval_text": item["retrieval_text"],
                    "table_refs": item["table_refs"],
                    "action_types": item["action_types"],
                    "params": item["params"],
                },
            )
        )

    if points:
        client.upsert(collection_name=collection_name, points=points)

    unique_sources = sorted({item["source"] for item in all_chunks})
    unique_objects = sorted({item["object_name"] for item in all_chunks})
    return {
        "knowledge_base_id": knowledge_base_id,
        "collection_name": collection_name,
        "chunk_count": len(all_chunks),
        "sources": unique_sources,
        "objects": unique_objects,
        "embedding_model": settings.embedding_model_name,
    }


def search_similar_chunks(query: str, top_k: int, knowledge_base_id: str):
    client = get_qdrant_client()
    collection_name = build_collection_name(knowledge_base_id)
    query_vector = embed_query(query)
    results = client.search(collection_name=collection_name, query_vector=query_vector, limit=top_k, with_payload=True)
    return results
