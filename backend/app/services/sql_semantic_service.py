"""SQL 语义解析、SQL 代码识别与细粒度逻辑切块服务。"""

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

SQL_OBJECT_START_PATTERN = re.compile(
    r"^\s*create\s+(?:or\s+alter\s+)?(?:proc(?:edure)?|view|trigger|table)\b",
    re.I | re.M,
)
SQL_FEATURE_PATTERN = re.compile(
    r"\b(create\s+(?:or\s+alter\s+)?(?:proc(?:edure)?|view|trigger|table)|select\b|insert\b|update\b|delete\b|merge\b|begin\b|end\b|if\b|else\b|case\b|join\b)\b",
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
            if any(pattern.search(stripped) for _, pattern in STATEMENT_START_PATTERNS if _ != "header"):
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


def describe_section(section: str) -> str:
    mapping = {
        "header": "参数定义、变量声明、初始化配置或过程入口说明",
        "query": "执行数据查询、关联分析或结果汇总",
        "branch_logic": "进行条件判断、分支控制或业务路径选择",
        "write_logic": "执行数据写入、更新、删除或合并",
        "return_logic": "设置输出参数、返回状态或返回结果",
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
