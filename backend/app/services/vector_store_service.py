"""Qdrant 向量存储服务。"""

from __future__ import annotations

from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, FieldCondition, Filter, MatchAny, MatchValue, PointStruct, VectorParams

from backend.app.config import settings
from backend.app.services.embedding_service import EmbeddingChannels, embed_for_channel, embed_query
from backend.app.services.sql_semantic_service import extract_sql_segments, parse_sql_chunks

_client: QdrantClient | None = None


RETRIEVAL_VECTOR_FIELD = EmbeddingChannels.RETRIEVAL
FUTURE_VECTOR_FIELDS = [EmbeddingChannels.SUMMARY]


def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        if settings.qdrant_url:
            _client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)
        else:
            _client = QdrantClient(path=str(settings.qdrant_path))
    return _client



def build_vector_config() -> VectorParams:
    vector_size = len(embed_query("test query", channel=EmbeddingChannels.RETRIEVAL))
    return VectorParams(size=vector_size, distance=Distance.COSINE)



def ensure_collection(collection_name: str) -> None:
    client = get_qdrant_client()
    collections = [item.name for item in client.get_collections().collections]
    if collection_name in collections:
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config=build_vector_config(),
    )



def build_collection_name(knowledge_base_id: str) -> str:
    return f"sql_kb_{knowledge_base_id.replace('-', '_')}"



def build_chunk_record(file_name: str, segment_index: int, chunk_index: int, chunk) -> dict:
    return {
        "source": file_name,
        "segment_index": segment_index,
        "chunk_index": chunk_index,
        "object_type": chunk.object_type,
        "object_name": chunk.object_name,
        "section": chunk.section,
        "tech_summary": chunk.tech_summary,
        "business_summary": chunk.business_summary,
        "raw_text": chunk.raw_text,
        "retrieval_text": chunk.retrieval_text,
        "table_refs": chunk.table_refs,
        "action_types": chunk.action_types,
        "params": chunk.params,
        "vector_channel": RETRIEVAL_VECTOR_FIELD,
        "future_vector_channels": FUTURE_VECTOR_FIELDS,
    }



def collect_sql_chunk_records(sql_texts: list[dict]) -> list[dict]:
    all_chunks = []
    for item in sql_texts:
        file_name = item["source"]
        segments = extract_sql_segments(item["text"])
        for segment_index, segment in enumerate(segments):
            chunks = parse_sql_chunks(segment)
            for chunk_index, chunk in enumerate(chunks):
                all_chunks.append(build_chunk_record(file_name, segment_index, chunk_index, chunk))
    return all_chunks



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
                        "tech_summary": chunk.tech_summary,
                        "business_summary": chunk.business_summary,
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
        "vector_strategy": {
            "active_channel": RETRIEVAL_VECTOR_FIELD,
            "future_channels": FUTURE_VECTOR_FIELDS,
        },
        "files": preview_items,
    }



def rebuild_sql_vectorstore(sql_texts: list[dict], knowledge_base_id: str):
    client = get_qdrant_client()
    collection_name = build_collection_name(knowledge_base_id)
    ensure_collection(collection_name)
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=build_vector_config(),
    )

    all_chunks = collect_sql_chunk_records(sql_texts)
    vectors = embed_for_channel(
        [item["retrieval_text"] for item in all_chunks],
        channel=EmbeddingChannels.RETRIEVAL,
    ) if all_chunks else []

    points = []
    for item, vector in zip(all_chunks, vectors):
        points.append(
            PointStruct(
                id=str(uuid4()),
                vector=vector,
                payload=item,
            )
        )

    if points:
        client.upsert(collection_name=collection_name, points=points)

    unique_sources = sorted({item["source"] for item in all_chunks})
    unique_objects = sorted({item["object_name"] for item in all_chunks})
    unique_table_refs = sorted({table for item in all_chunks for table in item["table_refs"]})
    return {
        "knowledge_base_id": knowledge_base_id,
        "collection_name": collection_name,
        "chunk_count": len(all_chunks),
        "sources": unique_sources,
        "objects": unique_objects,
        "table_refs": unique_table_refs,
        "embedding_model": settings.embedding_model_name,
        "vector_strategy": {
            "active_channel": RETRIEVAL_VECTOR_FIELD,
            "future_channels": FUTURE_VECTOR_FIELDS,
        },
    }



def build_search_filter(object_type: str | None = None, object_name: str | None = None, table_refs: list[str] | None = None):
    conditions = []
    if object_type:
        conditions.append(FieldCondition(key="object_type", match=MatchValue(value=object_type)))
    if object_name:
        conditions.append(FieldCondition(key="object_name", match=MatchValue(value=object_name)))
    if table_refs:
        conditions.append(FieldCondition(key="table_refs", match=MatchAny(any=table_refs)))
    return Filter(must=conditions) if conditions else None



def search_similar_chunks(
    query: str,
    top_k: int,
    knowledge_base_id: str,
    object_type: str | None = None,
    object_name: str | None = None,
    table_refs: list[str] | None = None,
):
    client = get_qdrant_client()
    collection_name = build_collection_name(knowledge_base_id)
    query_vector = embed_query(query, channel=EmbeddingChannels.RETRIEVAL)
    query_filter = build_search_filter(object_type=object_type, object_name=object_name, table_refs=table_refs)
    results = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True,
        query_filter=query_filter,
    )
    return results
