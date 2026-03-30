from backend.app.config import settings
from backend.app.services.llm_client import invoke_llm
from backend.app.services.vector_store_service import search_similar_chunks

QA_PROMPT_TEMPLATE = """浣犳槸涓€涓叕鍙稿唴閮ㄧ煡璇嗗簱闂瓟鍔╂墜銆?璇蜂弗鏍煎熀浜庣粰瀹氫笂涓嬫枃鍥炵瓟闂锛屼笉瑕佺紪閫犮€?濡傛灉涓婁笅鏂囦腑娌℃湁鏄庣‘绛旀锛岃鐩存帴鍥炵瓟鈥滅煡璇嗗簱涓病鏈夎冻澶熶俊鎭€濄€?
闂锛歿question}

涓婁笅鏂囷細
{context}

璇风粰鍑虹畝娲併€佸噯纭殑涓枃鍥炵瓟銆?"""

def answer_question(question: str, top_k: int | None = None) -> dict:
    k = top_k or settings.top_k
    results = search_similar_chunks(question, k)
    if not results:
        return {"answer": "鐭ヨ瘑搴撲腑娌℃湁瓒冲淇℃伅", "sources": [], "chunks": [], "score": []}

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
        context_parts.append(f"鏉ユ簮锛歿source}\n鍐呭锛歿chunk_text}")

    prompt = QA_PROMPT_TEMPLATE.format(question=question, context="\n\n".join(context_parts))
    answer = invoke_llm(prompt)
    return {
        "answer": answer,
        "sources": list(dict.fromkeys(sources)),
        "chunks": chunks,
        "score": scores,
    }
