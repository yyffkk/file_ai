"""大模型客户端封装。"""

from langchain_openai import ChatOpenAI

from backend.app.config import settings


def get_chat_model() -> ChatOpenAI:
    """创建聊天模型实例。"""

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not configured")

    return ChatOpenAI(
        model=settings.openai_chat_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=settings.temperature,
    )


def invoke_llm(prompt: str) -> str:
    """调用大模型并统一返回字符串结果。"""

    model = get_chat_model()
    response = model.invoke(prompt)
    return response.content if hasattr(response, "content") else str(response)
