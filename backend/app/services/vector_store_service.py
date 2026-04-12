"""Qdrant 向量存储服务。"""

from __future__ import annotations

from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

from backend.app.config import settings
from backend.app.services.embedding_service import embed_query, embed_texts
from backend.app.services.sql_semantic_service import extract_sql_segments, parse_sql_chunks

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


def preview_sql_chunks(sql_texts: list[dict], knowledge_base_id: str) -> dict:
    preview_items = []
    total_segments = 0
    total_chunks = 0

    for item in sql_texts:
        file_name = item["source"]
        segments = extract_sql_segments(item["text"])
        file_preview = {
            "source": file_name,
            "segment_count": len(segments),
            "segments": [],
        }
        total_segments += len(segments)

        for segment_index, segment in enumerate(segments):
            chunks = parse_sql_chunks(segment)
            total_chunks += len(chunks)
            segment_preview = {
                "segment_index": segment_index,
                "object_type": chunks[0].object_type if chunks else "SQL对象",
                "object_name": chunks[0].object_name if chunks else "unknown_object",
                "chunk_count": len(chunks),
                "raw_sql": segment,
                "chunks": [
                    {
                        "chunk_index": chunk_index,
                        "section": chunk.section,
                        "summary": chunk.summary,
                        "table_refs": chunk.table_refs,
                        "action_types": chunk.action_types,
                        "params": chunk.params,
                        "raw_text": chunk.raw_text,
                        "retrieval_text": chunk.retrieval_text,
                    }
                    for chunk_index, chunk in enumerate(chunks)
                ],
            }
            file_preview["segments"].append(segment_preview)

        preview_items.append(file_preview)

    return {
        "knowledge_base_id": knowledge_base_id,
        "file_count": len(preview_items),
        "segment_count": total_segments,
        "chunk_count": total_chunks,
        "files": preview_items,
    }


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
        segments = extract_sql_segments(item["text"])
        for segment_index, segment in enumerate(segments):
            chunks = parse_sql_chunks(segment)
            for chunk_index, chunk in enumerate(chunks):
                all_chunks.append({
                    "source": file_name,
                    "segment_index": segment_index,
                    "chunk_index": chunk_index,
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
                    "segment_index": item["segment_index"],
                    "chunk_index": item["chunk_index"],
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
