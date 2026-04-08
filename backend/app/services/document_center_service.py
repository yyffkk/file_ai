"""统一文档中心服务。

目标：
1. 提供统一上传入口
2. 一个文件可同时用于知识库和标书解析
3. 用最小代价兼容现有知识库/解析逻辑
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException

from backend.app.config import DOCUMENTS_DIR, PARSED_DIR, UPLOAD_DIR
from backend.app.services.knowledge_base_service import ensure_kb_exists, ensure_safe_filename, validate_extension

META_FILE = DOCUMENTS_DIR / "documents.meta.json"

FILE_STATUS_PENDING = "待处理"
FILE_STATUS_PROCESSING = "处理中"
FILE_STATUS_COMPLETED = "已完成"
FILE_STATUS_FAILED = "失败"

KB_STATUS_PENDING = "未构建"
KB_STATUS_PROCESSING = "构建中"
KB_STATUS_COMPLETED = "已完成"
KB_STATUS_FAILED = "失败"

PARSE_STATUS_PENDING = "待解析"
PARSE_STATUS_PROCESSING = "解析中"
PARSE_STATUS_COMPLETED = "已完成"
PARSE_STATUS_FAILED = "失败"


def _now() -> str:
    return datetime.now().isoformat()


def _read_meta() -> list[dict]:
    if not META_FILE.exists():
        return []
    try:
        return json.loads(META_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _write_meta(items: list[dict]) -> None:
    META_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def list_documents() -> list[dict]:
    items = _read_meta()
    return sorted(items, key=lambda item: item.get("created_at", ""), reverse=True)


def get_document(document_id: str) -> dict:
    for item in _read_meta():
        if item.get("id") == document_id:
            return item
    raise HTTPException(status_code=404, detail="Document not found")


def update_document(document_id: str, patch: dict) -> dict:
    items = _read_meta()
    for index, item in enumerate(items):
        if item.get("id") == document_id:
            item = {**item, **patch, "updated_at": _now()}
            items[index] = item
            _write_meta(items)
            return item
    raise HTTPException(status_code=404, detail="Document not found")


def create_document_record(file_name: str, size: int, enable_kb: bool, enable_parse: bool, knowledge_base_id: str | None) -> dict:
    safe_name = ensure_safe_filename(file_name)
    validate_extension(safe_name)

    document_id = uuid4().hex[:12]
    stored_name = f"{document_id}_{safe_name}"
    path = DOCUMENTS_DIR / stored_name
    now = _now()

    item = {
        "id": document_id,
        "name": safe_name,
        "stored_name": stored_name,
        "path": str(path),
        "size": size,
        "suffix": Path(safe_name).suffix.lower(),
        "knowledge_base_id": knowledge_base_id or "",
        "process_for_kb": enable_kb,
        "process_for_parse": enable_parse,
        "file_status": FILE_STATUS_PENDING,
        "knowledge_base_status": KB_STATUS_PENDING if enable_kb else "未启用",
        "parse_status": PARSE_STATUS_PENDING if enable_parse else "未启用",
        "parse_result_path": "",
        "error_message": "",
        "created_at": now,
        "updated_at": now,
    }

    items = _read_meta()
    items.append(item)
    _write_meta(items)
    return item


def save_document_content(document_id: str, content: bytes) -> dict:
    item = get_document(document_id)
    path = Path(item["path"])
    path.write_bytes(content)
    return update_document(document_id, {"file_status": FILE_STATUS_PROCESSING})


def attach_document_to_kb(document_id: str, knowledge_base_id: str) -> dict:
    item = get_document(document_id)
    ensure_kb_exists(knowledge_base_id)
    source = Path(item["path"])
    target = get_kb_file_path_for_copy(knowledge_base_id, item["name"])
    shutil.copyfile(source, target)
    return update_document(
        document_id,
        {
            "knowledge_base_id": knowledge_base_id,
            "process_for_kb": True,
            "knowledge_base_status": KB_STATUS_PENDING,
            "file_status": FILE_STATUS_PROCESSING if item.get("process_for_parse") else FILE_STATUS_COMPLETED,
        },
    )


def mark_parse_processing(document_id: str) -> dict:
    return update_document(document_id, {"parse_status": PARSE_STATUS_PROCESSING, "file_status": FILE_STATUS_PROCESSING})


def mark_parse_completed(document_id: str, parse_result_path: str) -> dict:
    item = get_document(document_id)
    kb_status = item.get("knowledge_base_status", "未启用")
    file_status = FILE_STATUS_COMPLETED if kb_status != KB_STATUS_FAILED else FILE_STATUS_FAILED
    return update_document(
        document_id,
        {
            "parse_status": PARSE_STATUS_COMPLETED,
            "parse_result_path": parse_result_path,
            "file_status": file_status,
            "error_message": "",
        },
    )


def mark_parse_failed(document_id: str, error_message: str) -> dict:
    return update_document(
        document_id,
        {
            "parse_status": PARSE_STATUS_FAILED,
            "file_status": FILE_STATUS_FAILED,
            "error_message": error_message,
        },
    )


def sync_kb_build_status(knowledge_base_id: str, status: str) -> None:
    items = _read_meta()
    changed = False
    for item in items:
        if item.get("knowledge_base_id") == knowledge_base_id and item.get("process_for_kb"):
            item["knowledge_base_status"] = status
            item["updated_at"] = _now()
            if item.get("parse_status") in ["未启用", PARSE_STATUS_COMPLETED, PARSE_STATUS_PENDING] and status != KB_STATUS_FAILED:
                item["file_status"] = FILE_STATUS_COMPLETED if status != KB_STATUS_PROCESSING else FILE_STATUS_PROCESSING
            elif status == KB_STATUS_FAILED:
                item["file_status"] = FILE_STATUS_FAILED
            changed = True
    if changed:
        _write_meta(items)


def get_parse_result(document_id: str) -> dict:
    item = get_document(document_id)
    result_path = item.get("parse_result_path")
    if not result_path:
        raise HTTPException(status_code=404, detail="Parse result not found")
    path = Path(result_path)
    if not path.exists():
        fallback = PARSED_DIR / f"{Path(item['name']).stem}.json"
        path = fallback
    if not path.exists():
        raise HTTPException(status_code=404, detail="Parse result file not found")
    return json.loads(path.read_text(encoding="utf-8"))


def get_kb_file_path_for_copy(knowledge_base_id: str, file_name: str) -> Path:
    ensure_kb_exists(knowledge_base_id)
    safe_name = ensure_safe_filename(file_name)
    return UPLOAD_DIR / knowledge_base_id / safe_name
