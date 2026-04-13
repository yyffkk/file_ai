"""SQL 语义解析、SQL 代码识别与细粒度逻辑切块服务。"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from backend.app.config import GENERATED_DIR, settings
from backend.app.services.llm_client import invoke_llm


@dataclass
class SQLChunk:
    object_type: str
    object_name: str
    section: str
    tech_summary: str
    business_summary: str
    raw_text: str
    retrieval_text: str
    table_refs: list[str]
    action_types: list[str]
    params: list[str]


OBJECT_PATTERNS = [
    ("存储过程", re.compile(r"create\s+(?:or\s+alter\s+)?proc(?:edure)?\s+(?:\[?\w+\]?\.)?(\[?\w+\]?)", re.I)),
    ("视图", re.compile(r"create\s+(?:or\s+alter\s+)?view\s+(?:\[?\w+\]?\.)?(\[?\w+\]?)", re.I)),
    ("触发器", re.compile(r"create\s+(?:or\s+alter\s+)?trigger\s+(?:\[?\w+\]?\.)?(\[?\w+\]?)", re.I)),
    ("表", re.compile(r"create\s+table\s+(?:\[?\w+\]?\.)?(\[?\w+\]?)", re.I)),
]

SQL_OBJECT_START_PATTERN = re.compile(
    r"^\s*create\s+(?:or\s+alter\s+)?(?:proc(?:edure)?|view|trigger|table)\b",
    re.I | re.M,
)
SQL_FEATURE_PATTERN = re.compile(
    r"\b(create\s+(?:or\s+alter\s+)?(?:proc(?:edure)?|view|trigger|table)|select\b|insert\b|update\b|delete\b|merge\b|begin\b|end\b|if\b|else\b|case\b|join\b|exists\b|where\b)\b",
    re.I,
)
TABLE_REF_PATTERN = re.compile(r"\b(?:from|join|update|into|merge\s+into|delete\s+from)\s+([\[\]\w\.]+)", re.I)
PARAM_PATTERN = re.compile(r"@\w+", re.I)
ACTION_PATTERNS = {
    "SELECT": re.compile(r"\bselect\b", re.I),
    "INSERT": re.compile(r"\binsert\b", re.I),
    "UPDATE": re.compile(r"\bupdate\b", re.I),
    "DELETE": re.compile(r"\bdelete\b", re.I),
    "MERGE": re.compile(r"\bmerge\b", re.I),
}
STATEMENT_START_PATTERNS = [
    ("branch_logic", re.compile(r"^\s*(if\b|else\b|case\b|when\b)", re.I)),
    ("write_logic", re.compile(r"^\s*(insert\b|update\b|delete\b|merge\b)", re.I)),
    ("return_logic", re.compile(r"^\s*(return\b|set\s+@\w+|select\s+@\w+)", re.I)),
    ("query", re.compile(r"^\s*select\b", re.I)),
    ("header", re.compile(r"^\s*(create\b|alter\b|as\b|declare\b|set\b|begin\b|@\w+)", re.I)),
]

SUMMARY_PROMPT_TEMPLATE = """你现在是一个“吊挂系统现场问题诊断专家 + 数据库语义分析专家 + RAG系统执行代理”。

你的任务是对一个 SQL 对象区段生成两类摘要，供后续数据库语义检索与现场问题诊断使用。

必须严格遵守：
1. 必须输出 JSON，且只能输出 JSON，不要解释。
2. JSON 结构必须为：
{
  "tech_summary": "...",
  "business_summary": "..."
}
3. tech_summary 必须包含：
   - 涉及表
   - SQL操作类型（SELECT/UPDATE/INSERT/DELETE/MERGE）
   - 条件逻辑
   - 返回参数或输出结果
4. business_summary 必须包含：
   - 该 SQL 在吊挂业务中的作用
   - 对应现场动作（如：出衣架、放行、扫码、工站过站、产线流转、主机联动、状态回传）
   - 失败时现场会看到什么现象
   - 使用业务词汇，如：工站、产线、主机、衣架、扫码、放行、初始化、绑定、过站
5. 禁止空泛描述，例如“处理数据”“执行查询”。
6. 如果区段信息不足，也必须明确写出“当前区段未体现xxx”，不能省略关键项。
7. 回答重点是给后续 RAG 检索和现场排障用，不是做学术解释。

输入信息：
对象类型: {object_type}
对象名称: {object_name}
区段类型: {section}
涉及表: {table_refs}
操作类型: {action_types}
参数: {params}
是否包含条件判断: {has_condition}
是否涉及返回结果: {has_return}
原始代码:
{raw_sql_chunk}
"""

SUMMARY_CACHE_FILE = GENERATED_DIR / "sql_summary_cache.json"


def load_summary_cache() -> dict:
    if not SUMMARY_CACHE_FILE.exists():
        return {}
    try:
        return json.loads(SUMMARY_CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}



def save_summary_cache(cache: dict) -> None:
    SUMMARY_CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")



def build_summary_cache_key(
    object_type: str,
    object_name: str,
    section: str,
    raw_sql_chunk: str,
    table_refs: list[str],
    action_types: list[str],
    params: list[str],
) -> str:
    payload = {
        "object_type": object_type,
        "object_name": object_name,
        "section": section,
        "raw_sql_chunk": raw_sql_chunk,
        "table_refs": table_refs,
        "action_types": action_types,
        "params": params,
        "model": settings.openai_chat_model,
        "base_url": settings.openai_base_url,
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()



def normalize_object_name(name: str) -> str:
    return name.strip().strip("[]")



def detect_object(sql_text: str) -> tuple[str, str]:
    for object_type, pattern in OBJECT_PATTERNS:
        match = pattern.search(sql_text)
        if match:
            return object_type, normalize_object_name(match.group(1))
    return "SQL对象", "unknown_object"



def is_likely_sql(text: str) -> bool:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return False
    score = 0
    if SQL_OBJECT_START_PATTERN.search(text):
        score += 5
    score += len(SQL_FEATURE_PATTERN.findall(text))
    return score >= 4



def extract_sql_segments(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n")
    matches = list(SQL_OBJECT_START_PATTERN.finditer(normalized))
    if matches:
        segments = []
        for index, match in enumerate(matches):
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
            segment = normalized[start:end].strip()
            if segment:
                segments.append(segment)
        return segments

    if is_likely_sql(normalized):
        return [normalized.strip()]
    return []



def split_sql_lines(sql_text: str) -> list[str]:
    return [line.rstrip() for line in sql_text.splitlines() if line.strip()]



def classify_statement(statement: str, fallback: str = "query") -> str:
    for section, pattern in STATEMENT_START_PATTERNS:
        if pattern.search(statement):
            return section
    return fallback



def split_statement_units(block_text: str, preferred_section: str) -> list[dict]:
    lines = split_sql_lines(block_text)
    if not lines:
        return []

    units: list[list[str]] = []
    current: list[str] = []
    begin_depth = 0
    case_depth = 0

    for line in lines:
        stripped = line.strip()
        upper = stripped.upper()
        starts_new = False

        if current and begin_depth == 0 and case_depth == 0:
            if any(pattern.search(stripped) for name, pattern in STATEMENT_START_PATTERNS if name != "header"):
                starts_new = True
            elif upper == "BEGIN":
                starts_new = True

        if starts_new:
            units.append(current)
            current = []

        current.append(line)

        begin_depth += len(re.findall(r"\bBEGIN\b", upper))
        begin_depth -= len(re.findall(r"\bEND\b", upper))
        case_depth += len(re.findall(r"\bCASE\b", upper))
        case_depth -= len(re.findall(r"\bEND\b", upper)) if "CASE" not in upper else 0
        begin_depth = max(begin_depth, 0)
        case_depth = max(case_depth, 0)

        if begin_depth == 0 and case_depth == 0 and stripped.endswith(";"):
            units.append(current)
            current = []

    if current:
        units.append(current)

    final_units = []
    for unit in units:
        raw_text = "\n".join(unit).strip()
        if raw_text:
            final_units.append({
                "section": classify_statement(raw_text, preferred_section),
                "raw_text": raw_text,
            })
    return final_units



def chunk_sql_by_logic(sql_text: str) -> tuple[str, str, list[dict]]:
    object_type, object_name = detect_object(sql_text)
    lines = split_sql_lines(sql_text)
    if not lines:
        return object_type, object_name, []

    blocks: list[dict] = []
    current_section = "header"
    current_lines: list[str] = []
    begin_depth = 0

    for line in lines:
        stripped = line.strip()
        line_section = classify_statement(stripped, current_section)
        opens_begin = bool(re.search(r"\bBEGIN\b", stripped, re.I))
        closes_end = bool(re.search(r"\bEND\b", stripped, re.I))
        should_split = False

        if current_lines and begin_depth == 0:
            if line_section != current_section and not closes_end:
                should_split = True
            elif re.search(r"^\s*if\b", stripped, re.I) or re.search(r"^\s*select\b", stripped, re.I) or re.search(r"^\s*(insert|update|delete|merge)\b", stripped, re.I):
                should_split = True

        if should_split:
            blocks.append({"section": current_section, "raw_text": "\n".join(current_lines).strip()})
            current_lines = []
            current_section = line_section

        current_lines.append(line)

        if opens_begin:
            begin_depth += len(re.findall(r"\bBEGIN\b", stripped, re.I))
        if closes_end:
            begin_depth -= len(re.findall(r"\bEND\b", stripped, re.I))
            begin_depth = max(begin_depth, 0)

        if begin_depth == 0 and stripped.upper() == "END" and current_lines:
            blocks.append({"section": current_section, "raw_text": "\n".join(current_lines).strip()})
            current_lines = []
            current_section = "query"

    if current_lines:
        blocks.append({"section": current_section, "raw_text": "\n".join(current_lines).strip()})

    refined_chunks: list[dict] = []
    for block in blocks:
        refined_chunks.extend(split_statement_units(block["raw_text"], block["section"]))

    return object_type, object_name, refined_chunks



def extract_table_refs(raw_sql_chunk: str) -> list[str]:
    refs = {item.strip().strip("[]") for item in TABLE_REF_PATTERN.findall(raw_sql_chunk)}
    return sorted(refs)



def extract_params(raw_sql_chunk: str) -> list[str]:
    return sorted(set(PARAM_PATTERN.findall(raw_sql_chunk)))



def extract_action_types(raw_sql_chunk: str) -> list[str]:
    return [name for name, pattern in ACTION_PATTERNS.items() if pattern.search(raw_sql_chunk)]



def has_condition(raw_sql_chunk: str) -> bool:
    return bool(re.search(r"\bif\b|\belse\b|\bcase\b|\bwhen\b|\bexists\b|\bwhere\b", raw_sql_chunk, re.I))



def has_return(raw_sql_chunk: str) -> bool:
    return bool(re.search(r"\breturn\b|\boutput\b|\bselect\s+@|\bset\s+@", raw_sql_chunk, re.I))



def build_rule_based_summaries(
    object_type: str,
    object_name: str,
    section: str,
    table_refs: list[str],
    action_types: list[str],
    params: list[str],
    raw_sql_chunk: str,
) -> tuple[str, str]:
    tables_text = "、".join(table_refs) if table_refs else "当前区段未识别到具体表"
    actions_text = "、".join(action_types) if action_types else "当前区段未识别到明确增删改查动作"
    params_text = "、".join(params) if params else "当前区段未识别到参数"
    condition_text = "包含条件判断" if has_condition(raw_sql_chunk) else "当前区段未体现明显条件判断"
    return_text = "包含返回参数或结果控制" if has_return(raw_sql_chunk) else "当前区段未体现明确返回参数或输出结果"

    tech_summary = (
        f"{object_type}{object_name}的{section}区段，涉及表：{tables_text}；"
        f"操作类型：{actions_text}；参数：{params_text}；{condition_text}；{return_text}。"
    )

    business_summary = (
        f"该区段属于吊挂业务相关数据库对象 {object_name} 的 {section} 逻辑。"
        f"从代码表象看，它用于支撑工站、产线、主机、衣架流转、扫码放行或状态判断中的某一环节。"
        f"如果这里条件不成立、数据未初始化、绑定关系错误或返回结果异常，现场可能出现扫码后无反应、工站不放行、衣架不流转、主机不联动、状态不回传等现象。"
        f"当前区段的业务信息有限，后续排障应结合表 {tables_text}、参数 {params_text} 和返回结果继续核对。"
    )

    return tech_summary, business_summary



def parse_summary_response(content: str) -> tuple[str, str] | None:
    try:
        data = json.loads(content)
    except Exception:
        match = re.search(r"\{.*\}", content, re.S)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except Exception:
            return None

    tech_summary = str(data.get("tech_summary", "")).strip()
    business_summary = str(data.get("business_summary", "")).strip()
    if not tech_summary or not business_summary:
        return None
    return re.sub(r"\s+", " ", tech_summary), re.sub(r"\s+", " ", business_summary)



def build_summaries(
    object_type: str,
    object_name: str,
    section: str,
    raw_sql_chunk: str,
    table_refs: list[str],
    action_types: list[str],
    params: list[str],
) -> tuple[str, str]:
    cache_key = build_summary_cache_key(
        object_type=object_type,
        object_name=object_name,
        section=section,
        raw_sql_chunk=raw_sql_chunk,
        table_refs=table_refs,
        action_types=action_types,
        params=params,
    )
    cache = load_summary_cache()
    cached_summary = cache.get(cache_key)
    if isinstance(cached_summary, dict):
        tech_summary = str(cached_summary.get("tech_summary", "")).strip()
        business_summary = str(cached_summary.get("business_summary", "")).strip()
        if tech_summary and business_summary:
            return tech_summary, business_summary

    summaries: tuple[str, str] | None = None

    prompt = SUMMARY_PROMPT_TEMPLATE.format(
        object_type=object_type,
        object_name=object_name,
        section=section,
        table_refs=", ".join(table_refs) if table_refs else "无",
        action_types=", ".join(action_types) if action_types else "无",
        params=", ".join(params) if params else "无",
        has_condition="是" if has_condition(raw_sql_chunk) else "否",
        has_return="是" if has_return(raw_sql_chunk) else "否",
        raw_sql_chunk=raw_sql_chunk,
    )

    if settings.sql_summary_use_llm:
        try:
            llm_response = invoke_llm(prompt).strip()
            summaries = parse_summary_response(llm_response)
        except Exception:
            summaries = None

    if not summaries:
        summaries = build_rule_based_summaries(
            object_type=object_type,
            object_name=object_name,
            section=section,
            table_refs=table_refs,
            action_types=action_types,
            params=params,
            raw_sql_chunk=raw_sql_chunk,
        )

    cache[cache_key] = {
        "tech_summary": summaries[0],
        "business_summary": summaries[1],
    }
    save_summary_cache(cache)
    return summaries



def build_retrieval_text(
    object_type: str,
    object_name: str,
    section: str,
    tech_summary: str,
    business_summary: str,
    table_refs: list[str],
    action_types: list[str],
    params: list[str],
    raw_sql_chunk: str,
) -> str:
    return (
        f"对象类型: {object_type}\n"
        f"对象名称: {object_name}\n"
        f"区段: {section}\n\n"
        f"技术摘要:\n{tech_summary}\n\n"
        f"业务摘要:\n{business_summary}\n\n"
        f"涉及表:\n{', '.join(table_refs) if table_refs else '无'}\n\n"
        f"操作类型:\n{', '.join(action_types) if action_types else '无'}\n\n"
        f"参数:\n{', '.join(params) if params else '无'}\n\n"
        f"原始代码:\n{raw_sql_chunk}"
    )



def parse_sql_chunks(sql_text: str) -> list[SQLChunk]:
    object_type, object_name, chunks = chunk_sql_by_logic(sql_text)
    final_chunks: list[SQLChunk] = []

    for chunk in chunks:
        raw_text = chunk["raw_text"].strip()
        if not raw_text:
            continue
        table_refs = extract_table_refs(raw_text)
        action_types = extract_action_types(raw_text)
        params = extract_params(raw_text)
        tech_summary, business_summary = build_summaries(
            object_type,
            object_name,
            chunk["section"],
            raw_text,
            table_refs,
            action_types,
            params,
        )
        retrieval_text = build_retrieval_text(
            object_type=object_type,
            object_name=object_name,
            section=chunk["section"],
            tech_summary=tech_summary,
            business_summary=business_summary,
            table_refs=table_refs,
            action_types=action_types,
            params=params,
            raw_sql_chunk=raw_text,
        )
        final_chunks.append(
            SQLChunk(
                object_type=object_type,
                object_name=object_name,
                section=chunk["section"],
                tech_summary=tech_summary,
                business_summary=business_summary,
                raw_text=raw_text,
                retrieval_text=retrieval_text,
                table_refs=table_refs,
                action_types=action_types,
                params=params,
            )
        )

    return final_chunks
