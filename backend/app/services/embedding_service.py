"""Embedding 服务封装，基于 fastembed。"""

from __future__ import annotations

from fastembed import TextEmbedding

from backend.app.config import settings

_embedding_model: TextEmbedding | None = None


def get_embedding_model() -> TextEmbedding:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = TextEmbedding(model_name=settings.embedding_model_name)
    return _embedding_model


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    return [list(vector) for vector in model.embed(texts)]


def embed_query(text: str) -> list[float]:
    model = get_embedding_model()
    return list(next(model.query_embed(text)))
