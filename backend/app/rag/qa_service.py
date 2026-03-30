from backend.app.config import settings
from backend.app.services.llm_client import invoke_llm
from backend.app.services.vector_store_service import search_similar_chunks

QA_PROMPT_TEMPLATE = """You are an internal knowledge base assistant.
Answer strictly based on the provided context.
If the answer is not available in the context, reply with: Not enough information in the knowledge base.

Question:
{question}

Context:
{context}

Return a concise and accurate answer.
"""


def answer_question(question: str, top_k: int | None = None) -> dict:
    k = top_k or settings.top_k
    results = search_similar_chunks(question, k)

    if not results:
        return {
            "answer": "Not enough information in the knowledge base.",
            "sources": [],
            "chunks": [],
            "score": [],
        }

    chunks = []
    sources = []
    scores = []
    context_parts = []

    for doc, score in results:
        chunk_text = doc.page_content.strip()
        source = doc.metadata.get("source", "")
        chunks.append(chunk_text)
        sources.append(source)
        scores.append(float(score))
        context_parts.append(f"Source: {source}\nContent: {chunk_text}")

    prompt = QA_PROMPT_TEMPLATE.format(question=question, context="\n\n".join(context_parts))
    answer = invoke_llm(prompt)

    return {
        "answer": answer,
        "sources": list(dict.fromkeys(sources)),
        "chunks": chunks,
        "score": scores,
    }
