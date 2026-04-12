"""SQL 知识库问答服务。"""

from backend.app.config import settings
from backend.app.services.llm_client import invoke_llm
from backend.app.services.vector_store_service import search_similar_chunks

QA_PROMPT_TEMPLATE = """你是数据库语义解析助手。
请基于检索到的 SQL 摘要和原始代码回答问题。
优先依据 summary 做语义定位，再结合 raw_text 做解释。
如果上下文不足，请明确说“知识库中没有足够信息”。

问题:
{question}

上下文:
{context}

请输出简洁、准确、可解释的答案。
"""


def answer_question(knowledge_base_id: str, question: str, top_k: int | None = None) -> dict:
    k = top_k or settings.top_k
    results = search_similar_chunks(question, k, knowledge_base_id)

    if not results:
        return {
            "answer": "知识库中没有足够信息。",
            "sources": [],
            "chunks": [],
            "score": [],
        }

    chunks = []
    sources = []
    scores = []
    context_parts = []

    for item in results:
        payload = item.payload or {}
        raw_text = payload.get("raw_text", "")
        summary = payload.get("summary", "")
        source = payload.get("source", "")
        object_name = payload.get("object_name", "")
        section = payload.get("section", "")
        chunks.append(raw_text)
        sources.append(source)
        scores.append(float(item.score))
        context_parts.append(
            f"对象: {object_name}\n区段: {section}\n摘要: {summary}\n原始代码: {raw_text}"
        )

    prompt = QA_PROMPT_TEMPLATE.format(question=question, context="\n\n".join(context_parts))
    answer = invoke_llm(prompt)

    return {
        "answer": answer,
        "sources": list(dict.fromkeys(sources)),
        "chunks": chunks,
        "score": scores,
    }
