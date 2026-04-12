"""文档加载器。

负责把 txt/doc/docx/pdf/sql 统一转换成纯文本，供 SQL 知识库构建使用。
"""

from pathlib import Path

from docx import Document
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".txt", ".doc", ".docx", ".pdf", ".sql"}


def load_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def load_sql(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def load_docx(path: Path) -> str:
    doc = Document(str(path))
    return "\n".join([p.text for p in doc.paragraphs if p.text and p.text.strip()])


def load_doc(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def load_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    texts = []
    for page in reader.pages:
        texts.append(page.extract_text() or "")
    return "\n".join(texts)


def load_document_text(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix}")
    if suffix == ".txt":
        return load_txt(path)
    if suffix == ".sql":
        return load_sql(path)
    if suffix == ".doc":
        return load_doc(path)
    if suffix == ".docx":
        return load_docx(path)
    if suffix == ".pdf":
        return load_pdf(path)

    raise ValueError(f"Unsupported file type: {suffix}")
