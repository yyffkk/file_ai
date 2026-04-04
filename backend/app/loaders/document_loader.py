"""文档加载器。

负责把 txt/docx/pdf 统一转换成纯文本，供知识库构建和标书解析复用。
"""

from pathlib import Path

from docx import Document
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".txt", ".docx", ".pdf"}


def load_txt(path: Path) -> str:
    """读取 txt 文本。"""

    return path.read_text(encoding="utf-8", errors="ignore")


def load_docx(path: Path) -> str:
    """抽取 docx 正文段落。"""

    doc = Document(str(path))
    return "\n".join([p.text for p in doc.paragraphs if p.text and p.text.strip()])


def load_pdf(path: Path) -> str:
    """逐页抽取 PDF 文本。"""

    reader = PdfReader(str(path))
    texts = []
    for page in reader.pages:
        texts.append(page.extract_text() or "")
    return "\n".join(texts)


def load_document_text(path: Path) -> str:
    """根据扩展名自动选择对应的加载器。"""

    suffix = path.suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix}")
    if suffix == ".txt":
        return load_txt(path)
    if suffix == ".docx":
        return load_docx(path)
    if suffix == ".pdf":
        return load_pdf(path)

    raise ValueError(f"Unsupported file type: {suffix}")
