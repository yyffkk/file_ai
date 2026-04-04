"""Embedding 服务封装。"""

from langchain_openai import OpenAIEmbeddings

from backend.app.config import settings


def get_embeddings() -> OpenAIEmbeddings:
    """创建 Embedding 客户端。"""

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not configured")

    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )
