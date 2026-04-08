"""AI 写标书服务。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from backend.app.config import GENERATED_DIR, settings
from backend.app.services.llm_client import invoke_llm
from backend.app.services.vector_store_service import search_similar_chunks

WRITER_PROMPT = """你是一个专业的投标文件写作助手。请基于提供的项目需求和资料库片段，生成一份结构清晰、可继续编辑的投标文件初稿。

要求：
1. 严格优先参考资料库内容，不要凭空编造关键事实。
2. 如果某些信息资料中没有，请使用“【待补充】”标记，而不是乱写。
3. 输出采用中文，结构清晰，适合作为标书初稿继续编辑。
4. 至少包含以下章节：
   - 项目理解
   - 技术方案
   - 实施计划
   - 质量保障
   - 售后服务
   - 商务响应
5. 最后附一段“待确认信息清单”。

项目名称：
{project_name}

招标需求：
{requirement_text}

资料库参考片段：
{context}

请直接输出可编辑的标书正文，不要输出 JSON，不要解释。"""


def build_writer_context(knowledge_base_id: str, requirement_text: str, top_k: int | None = None) -> dict:
    k = top_k or settings.top_k
    query = requirement_text or "请根据资料库生成适配该项目的投标文件"
    results = search_similar_chunks(query, k, knowledge_base_id)

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
        context_parts.append(f"来源文件: {source}\n内容: {chunk_text}")

    return {
        "chunks": chunks,
        "sources": list(dict.fromkeys(sources)),
        "scores": scores,
        "context": "\n\n".join(context_parts),
    }


def generate_tender_draft(project_name: str, requirement_text: str, knowledge_base_id: str, top_k: int | None = None) -> dict:
    context_data = build_writer_context(knowledge_base_id, requirement_text, top_k)
    prompt = WRITER_PROMPT.format(
        project_name=project_name,
        requirement_text=requirement_text or "【未提供详细需求，请结合资料生成通用初稿】",
        context=context_data["context"] or "【资料库暂无可用片段】",
    )
    content = invoke_llm(prompt)

    return {
        "project_name": project_name,
        "knowledge_base_id": knowledge_base_id,
        "requirement_text": requirement_text,
        "content": content,
        "sources": context_data["sources"],
        "chunks": context_data["chunks"],
        "scores": context_data["scores"],
        "generated_at": datetime.now().isoformat(),
    }


def list_generated_results() -> list[dict]:
    items = []
    for path in sorted(GENERATED_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            items.append(
                {
                    "id": data.get("id", path.stem),
                    "project_name": data.get("project_name", path.stem),
                    "knowledge_base_id": data.get("knowledge_base_id", ""),
                    "updated_at": data.get("updated_at", data.get("generated_at", "")),
                    "file_name": path.name,
                }
            )
        except Exception:
            continue
    return items


def save_generated_result(project_name: str, content: str, knowledge_base_id: str) -> dict:
    item_id = uuid4().hex[:12]
    now = datetime.now().isoformat()
    data = {
        "id": item_id,
        "project_name": project_name,
        "knowledge_base_id": knowledge_base_id,
        "content": content,
        "generated_at": now,
        "updated_at": now,
    }
    path = GENERATED_DIR / f"{item_id}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def get_generated_result(result_id: str) -> dict:
    path = GENERATED_DIR / f"{result_id}.json"
    if not path.exists():
        raise FileNotFoundError("Generated result not found")
    return json.loads(path.read_text(encoding="utf-8"))
