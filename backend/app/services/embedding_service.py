"""Embedding 服务封装，基于 fastembed。"""

from __future__ import annotations

from fastembed import TextEmbedding

from backend.app.config import settings

_embedding_model: TextEmbedding | None = None


class EmbeddingChannels:
    """为后续多通道向量检索预留扩展点。"""

    RETRIEVAL = "retrieval_text"
    SUMMARY = "summary"


def get_embedding_model() -> TextEmbedding:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = TextEmbedding(model_name=settings.embedding_model_name)
    return _embedding_model


def embed_for_channel(texts: list[str], channel: str = EmbeddingChannels.RETRIEVAL) -> list[list[float]]:
    if channel != EmbeddingChannels.RETRIEVAL:
        raise ValueError(f"Embedding channel not enabled yet: {channel}")
    model = get_embedding_model()
    return [list(vector) for vector in model.embed(texts)]


def embed_query(text: str, channel: str = EmbeddingChannels.RETRIEVAL) -> list[float]:
    if channel != EmbeddingChannels.RETRIEVAL:
        raise ValueError(f"Embedding channel not enabled yet: {channel}")
    model = get_embedding_model()
    return list(next(model.query_embed(text)))
