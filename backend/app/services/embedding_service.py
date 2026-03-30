from langchain_openai import OpenAIEmbeddings
from backend.app.config import settings

def get_embeddings() -> OpenAIEmbeddings:
    if not settings.openai_api_key:
        raise ValueError("鏈厤缃?OPENAI_API_KEY")
    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )
