"""SQL 语义解析与逻辑切块服务。"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SQLChunk:
    object_type: str
    object_name: str
    section: str
    summary: str
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

SECTION_RULES = [
    ("header", re.compile(r"\b(as|declare|set|begin)\b|^\s*@", re.I)),
    ("branch_logic", re.compile(r"\bif\b|\belse\b|\bcase\b|\bwhen\b", re.I)),
    ("write_logic", re.compile(r"\binsert\b|\bupdate\b|\bdelete\b|\bmerge\b", re.I)),
    ("return_logic", re.compile(r"\breturn\b|\boutput\b|\bselect\b.+@|\bset\s+@", re.I)),
    ("query", re.compile(r"\bselect\b", re.I)),
]

TABLE_REF_PATTERN = re.compile(r"\b(?:from|join|update|into|merge\s+into|delete\s+from)\s+([\[\]\w\.]+)", re.I)
PARAM_PATTERN = re.compile(r"@\w+", re.I)
ACTION_PATTERNS = {
    "SELECT": re.compile(r"\bselect\b", re.I),
    "INSERT": re.compile(r"\binsert\b", re.I),
    "UPDATE": re.compile(r"\bupdate\b", re.I),
    "DELETE": re.compile(r"\bdelete\b", re.I),
    "MERGE": re.compile(r"\bmerge\b", re.I),
}


def normalize_object_name(name: str) -> str:
    return name.strip().strip("[]")


def detect_object(sql_text: str) -> tuple[str, str]:
    for object_type, pattern in OBJECT_PATTERNS:
        match = pattern.search(sql_text)
        if match:
            return object_type, normalize_object_name(match.group(1))
    return "SQL对象", "unknown_object"


def split_sql_lines(sql_text: str) -> list[str]:
    return [line.rstrip() for line in sql_text.splitlines() if line.strip()]


def detect_section(line: str) -> str:
    for section, pattern in SECTION_RULES:
        if pattern.search(line):
            return section
    return "query"


def chunk_sql_by_logic(sql_text: str) -> tuple[str, str, list[dict]]:
    object_type, object_name = detect_object(sql_text)
    lines = split_sql_lines(sql_text)
    if not lines:
        return object_type, object_name, []

    chunks: list[dict] = []
    current_section = detect_section(lines[0])
    current_lines: list[str] = []

    for line in lines:
        line_section = detect_section(line)
        if current_lines and line_section != current_section:
            chunks.append({"section": current_section, "raw_text": "\n".join(current_lines).strip()})
            current_lines = [line]
            current_section = line_section
        else:
            current_lines.append(line)

    if current_lines:
        chunks.append({"section": current_section, "raw_text": "\n".join(current_lines).strip()})

    merged_chunks: list[dict] = []
    for chunk in chunks:
        if merged_chunks and chunk["section"] == merged_chunks[-1]["section"]:
            merged_chunks[-1]["raw_text"] += "\n" + chunk["raw_text"]
        else:
            merged_chunks.append(chunk)

    return object_type, object_name, merged_chunks


def extract_table_refs(raw_sql_chunk: str) -> list[str]:
    refs = {item.strip().strip("[]") for item in TABLE_REF_PATTERN.findall(raw_sql_chunk)}
    return sorted(refs)


def extract_params(raw_sql_chunk: str) -> list[str]:
    return sorted(set(PARAM_PATTERN.findall(raw_sql_chunk)))


def extract_action_types(raw_sql_chunk: str) -> list[str]:
    actions = [name for name, pattern in ACTION_PATTERNS.items() if pattern.search(raw_sql_chunk)]
    return actions


def has_condition(raw_sql_chunk: str) -> bool:
    return bool(re.search(r"\bif\b|\belse\b|\bcase\b|\bwhen\b|\bexists\b|\bwhere\b", raw_sql_chunk, re.I))


def has_return(raw_sql_chunk: str) -> bool:
    return bool(re.search(r"\breturn\b|\boutput\b|\bselect\b.+@|\bset\s+@", raw_sql_chunk, re.I))


def describe_section(section: str) -> str:
    mapping = {
        "header": "参数定义、变量声明或初始化配置",
        "query": "执行数据查询或结果汇总",
        "branch_logic": "进行条件判断与分支控制",
        "write_logic": "执行数据写入、更新或删除",
        "return_logic": "设置返回参数或输出结果",
    }
    return mapping.get(section, "执行数据库逻辑")


def build_summary(
    object_type: str,
    object_name: str,
    section: str,
    raw_sql_chunk: str,
    table_refs: list[str],
    action_types: list[str],
    params: list[str],
) -> str:
    condition_text = "包含条件判断" if has_condition(raw_sql_chunk) else "不包含明显条件判断"
    return_text = "涉及返回结果" if has_return(raw_sql_chunk) else "未直接体现返回结果"
    tables_text = "、".join(table_refs) if table_refs else "未识别到具体表"
    actions_text = "、".join(action_types) if action_types else "无明确数据操作"
    params_text = f"参数包括 {'、'.join(params)}。" if params else "未识别到参数。"

    return (
        f"该代码块属于{object_type} {object_name}，"
        f"当前区段为{section}。"
        f"该逻辑主要用于{describe_section(section)}，"
        f"涉及表 {tables_text}，"
        f"包含 {actions_text} 操作，"
        f"{condition_text}，"
        f"{return_text}。"
        f"{params_text}"
    )


def build_retrieval_text(
    object_type: str,
    object_name: str,
    section: str,
    summary: str,
    table_refs: list[str],
    action_types: list[str],
    params: list[str],
    raw_sql_chunk: str,
) -> str:
    return (
        f"对象类型: {object_type}\n"
        f"对象名称: {object_name}\n"
        f"区段: {section}\n\n"
        f"摘要:\n{summary}\n\n"
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
        summary = build_summary(object_type, object_name, chunk["section"], raw_text, table_refs, action_types, params)
        retrieval_text = build_retrieval_text(
            object_type=object_type,
            object_name=object_name,
            section=chunk["section"],
            summary=summary,
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
                summary=summary,
                raw_text=raw_text,
                retrieval_text=retrieval_text,
                table_refs=table_refs,
                action_types=action_types,
                params=params,
            )
        )

    return final_chunks
