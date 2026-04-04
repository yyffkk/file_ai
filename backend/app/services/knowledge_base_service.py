"""知识库目录、文件和元数据管理。

这个模块把“多知识库”的目录约定统一封装起来，避免 API 层到处拼路径。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException

from backend.app.config import UPLOAD_DIR, VECTORSTORE_DIR

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')
META_FILE_NAME = "kb.meta.json"


def slugify_kb_name(name: str) -> str:
    """把中文/英文名称转换成可读的 slug 片段。"""

    normalized = re.sub(r"\s+", "-", name.strip().lower())
    normalized = re.sub(r"[^a-z0-9\u4e00-\u9fa5_-]", "-", normalized)
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "knowledge-base"


def build_knowledge_base_id(name: str) -> str:
    """生成内部 ID。

    这里把“显示名”和“内部ID”分开：
    - name: 给人看
    - id: 给系统做目录和接口标识
    """

    slug = slugify_kb_name(name)
    short_id = uuid4().hex[:8]
    return f"{slug}-{short_id}"


def get_meta_path(kb_dir: Path) -> Path:
    """返回知识库元数据文件路径。"""

    return kb_dir / META_FILE_NAME


def build_default_meta(kb_dir: Path) -> dict:
    """给历史知识库构造默认元数据。"""

    return {
        "id": kb_dir.name,
        "name": kb_dir.name,
        "created_at": datetime.fromtimestamp(kb_dir.stat().st_ctime).isoformat(),
        "migrated": True,
    }


def read_kb_meta(kb_dir: Path) -> dict:
    """读取知识库元数据；老目录没有元数据时自动兼容。"""

    meta_path = get_meta_path(kb_dir)
    default_meta = build_default_meta(kb_dir)

    if not meta_path.exists():
        return default_meta

    try:
        content = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return default_meta

    return {
        "id": content.get("id", kb_dir.name),
        "name": content.get("name", kb_dir.name),
        "created_at": content.get("created_at", default_meta["created_at"]),
        "migrated": content.get("migrated", False),
    }


def write_kb_meta(kb_dir: Path, meta: dict) -> None:
    """写入知识库元数据。"""

    get_meta_path(kb_dir).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def migrate_legacy_knowledge_bases() -> dict:
    """扫描 uploads 目录，为缺失元数据的历史知识库补齐 kb.meta.json。"""

    migrated = []
    skipped = []

    for kb_dir in sorted(UPLOAD_DIR.iterdir(), key=lambda item: item.name.lower()):
        if not kb_dir.is_dir():
            continue

        meta_path = get_meta_path(kb_dir)
        if meta_path.exists():
            skipped.append(kb_dir.name)
            continue

        meta = build_default_meta(kb_dir)
        write_kb_meta(kb_dir, meta)
        migrated.append({"id": meta["id"], "name": meta["name"]})

    return {
        "migrated_count": len(migrated),
        "migrated_items": migrated,
        "skipped_count": len(skipped),
    }


def ensure_kb_exists(knowledge_base_id: str) -> Path:
    """校验知识库是否存在，不存在则抛 404。"""

    kb_dir = UPLOAD_DIR / knowledge_base_id
    if not kb_dir.exists() or not kb_dir.is_dir():
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb_dir


def ensure_safe_filename(file_name: str) -> str:
    """过滤危险文件名，避免路径穿越和系统非法字符。"""

    clean_name = Path(file_name).name.strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="Invalid file name")
    if INVALID_FILENAME_CHARS.search(clean_name):
        raise HTTPException(status_code=400, detail="Invalid file name")
    return clean_name


def validate_extension(file_name: str) -> str:
    """校验扩展名，仅允许当前 MVP 支持的文本类文档。"""

    suffix = Path(file_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only pdf, docx and txt files are supported")
    return suffix


def create_knowledge_base(name: str) -> dict:
    """创建知识库目录，并返回前端需要展示的基础信息。"""

    display_name = name.strip()
    if not display_name:
        raise HTTPException(status_code=400, detail="Knowledge base name is required")

    knowledge_base_id = build_knowledge_base_id(display_name)
    kb_dir = UPLOAD_DIR / knowledge_base_id

    if kb_dir.exists():
        raise HTTPException(status_code=409, detail="Knowledge base already exists")

    kb_dir.mkdir(parents=True, exist_ok=False)
    meta = {
        "id": knowledge_base_id,
        "name": display_name,
        "created_at": datetime.fromtimestamp(kb_dir.stat().st_ctime).isoformat(),
        "migrated": False,
    }
    write_kb_meta(kb_dir, meta)

    return {
        **meta,
        "file_count": 0,
    }


def list_knowledge_bases() -> list[dict]:
    """返回全部知识库列表。

    顺手自动补齐历史目录的元数据，避免旧数据永远停留在兼容模式。
    """

    migrate_legacy_knowledge_bases()

    knowledge_bases = []
    for kb_dir in sorted(UPLOAD_DIR.iterdir(), key=lambda item: item.name.lower()):
        if not kb_dir.is_dir():
            continue

        meta = read_kb_meta(kb_dir)
        files = [
            path
            for path in kb_dir.iterdir()
            if path.is_file() and path.name != META_FILE_NAME and path.suffix.lower() in ALLOWED_EXTENSIONS
        ]
        knowledge_bases.append(
            {
                "id": meta["id"],
                "name": meta["name"],
                "file_count": len(files),
                "created_at": meta["created_at"],
                "migrated": meta.get("migrated", False),
            }
        )

    return knowledge_bases


def list_kb_files(knowledge_base_id: str) -> list[dict]:
    """列出某个知识库下的文件，供前端展示、预览和下载。"""

    kb_dir = ensure_kb_exists(knowledge_base_id)
    items = []

    for path in sorted(kb_dir.iterdir(), key=lambda item: item.name.lower()):
        if not path.is_file() or path.name == META_FILE_NAME or path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue

        stat = path.stat()
        items.append(
            {
                "name": path.name,
                "size": stat.st_size,
                "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "suffix": path.suffix.lower(),
            }
        )

    return items


def get_kb_file_path(knowledge_base_id: str, file_name: str) -> Path:
    """获取知识库文件真实路径，并校验该文件属于目标知识库。"""

    kb_dir = ensure_kb_exists(knowledge_base_id)
    safe_name = ensure_safe_filename(file_name)
    path = kb_dir / safe_name
    if not path.exists() or not path.is_file() or path.name == META_FILE_NAME:
        raise HTTPException(status_code=404, detail="File not found")
    return path


def get_vectorstore_path(knowledge_base_id: str) -> Path:
    """每个知识库对应独立向量索引目录。"""

    return VECTORSTORE_DIR / knowledge_base_id
