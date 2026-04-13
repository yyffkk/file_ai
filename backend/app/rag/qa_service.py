"""SQL 知识库问答服务。"""

from backend.app.config import settings
from backend.app.services.llm_client import invoke_llm
from backend.app.services.vector_store_service import search_similar_chunks

QA_PROMPT_TEMPLATE = """你现在不是普通问答助手。
你是一个“吊挂系统现场问题诊断专家 + 数据库语义分析专家 + RAG系统执行代理”。

你的任务：
通过分析数据库对象（存储过程、视图、触发器、表结构）以及业务语义，帮助用户解决车间现场问题。

你必须遵守以下原则：
1. 先用 business_summary 理解业务，再用 tech_summary 理解 SQL 逻辑。
2. 必要时可以引用原始 SQL，但不能只解释代码。
3. 不允许编造表、字段、业务流程、主机关系、工站关系。
4. 如果上下文不足，必须明确指出“知识库中没有足够信息支撑该结论”，并说明还缺什么。
5. 回答必须让现场人员知道怎么查、查什么、怎么修。

当问题像“为什么不能放行”“为什么扫完码没反应”“为什么衣架不走”“为什么工站没过站”“为什么主机不联动”这类现场问题时，必须尽量按下面结构输出：

【1. 现象理解】
用业务语言解释问题本质

【2. 可能原因（业务层）】
列出 2~4 个可能原因

【3. 相关数据库对象】
列出相关表、存储过程、字段

【4. SQL逻辑解释】
说明哪个条件控制行为，哪个字段决定结果

【5. 排查步骤】
必须给出可执行步骤

【6. 排查SQL】
必须给出可执行 SQL；若上下文不足无法精确写字段名，要明确标注“字段名需按实际库核对”

【7. 修复建议】
给出可落地修复建议

如果用户不是在提现场故障，而是在问对象作用、过程含义、逻辑关系，也要用业务语言回答，不要学术化。

问题:
{question}

上下文:
{context}

请输出面向车间排障和数据库排查的答案。"""


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
        tech_summary = payload.get("tech_summary", "")
        business_summary = payload.get("business_summary", "")
        source = payload.get("source", "")
        object_name = payload.get("object_name", "")
        object_type = payload.get("object_type", "")
        section = payload.get("section", "")
        table_refs = payload.get("table_refs", [])
        action_types = payload.get("action_types", [])
        params = payload.get("params", [])

        chunks.append(raw_text)
        sources.append(source)
        scores.append(float(item.score))
        context_parts.append(
            f"对象类型: {object_type}\n"
            f"对象: {object_name}\n"
            f"区段: {section}\n"
            f"业务摘要: {business_summary}\n"
            f"技术摘要: {tech_summary}\n"
            f"涉及表: {', '.join(table_refs) if table_refs else '无'}\n"
            f"操作类型: {', '.join(action_types) if action_types else '无'}\n"
            f"参数: {', '.join(params) if params else '无'}\n"
            f"原始代码: {raw_text}"
        )

    prompt = QA_PROMPT_TEMPLATE.format(question=question, context="\n\n".join(context_parts))
    answer = invoke_llm(prompt)

    return {
        "answer": answer,
        "sources": list(dict.fromkeys(sources)),
        "chunks": chunks,
        "score": scores,
    }
