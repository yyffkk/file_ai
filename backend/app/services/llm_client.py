from langchain_openai import ChatOpenAI

from backend.app.config import settings


def get_chat_model() -> ChatOpenAI:
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not configured")

    return ChatOpenAI(
        model=settings.openai_chat_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=settings.temperature,
    )


def invoke_llm(prompt: str) -> str:
    model = get_chat_model()
    response = model.invoke(prompt)
    return response.content if hasattr(response, "content") else str(response)
