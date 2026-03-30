$base = 'D:\python_project\langchain_tender_mvp'

$files = @{
'README.md' = @'
# LangChain 知识库 + 标书解析 MVP

这是一个可直接运行的最小项目，包含两块能力：

1. **知识库问答**：上传文档、切分、向量化、FAISS 入库、检索问答
2. **标书解析**：上传 PDF / DOCX / TXT 招标文件，提取文本、粗拆章节、调用 LLM 输出结构化 JSON

## 1. 技术栈
- Python 3.11
- FastAPI
- LangChain
- FAISS（本地）
- pypdf / python-docx
- 本地文件 + JSON

## 2. 项目结构
```text
backend/
  app/
    api/
      knowledge_base.py
      tender_parser.py
    loaders/
      document_loader.py
    parsers/
      tender_parser.py
    prompts/
      tender_extract_prompt.py
    rag/
      qa_service.py
    schemas/
      common.py
      knowledge_base.py
      tender_parser.py
    services/
      embedding_service.py
      llm_client.py
      text_splitter_service.py
      vector_store_service.py
    config.py
    main.py
  data/
    uploads/
    parsed/
    vectorstore/
.env.example
requirements.txt
README.md
```

## 3. 快速启动
### 3.1 创建虚拟环境
```bash
cd D:\python_project\langchain_tender_mvp
python -m venv .venv
.venv\Scripts\activate
```

### 3.2 安装依赖
```bash
pip install -r requirements.txt
```

### 3.3 配置环境变量
复制 `.env.example` 为 `.env`，至少配置：
```env
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
TEMPERATURE=0
TOP_K=4
```

### 3.4 启动服务
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

启动后打开：
- Swagger: <http://127.0.0.1:8000/docs>
- 健康检查: <http://127.0.0.1:8000/health>

## 4. 测试顺序
1. `/api/kb/upload` 上传文档
2. `/api/kb/build` 构建知识库
3. `/api/kb/ask` 做问答
4. `/api/tender/parse` 解析标书
5. 检查 `backend/data/parsed/` 输出 JSON

## 5. 当前边界
- PDF 仅支持文本型 PDF，不做 OCR
- 章节切分为规则粗拆分
- 字段抽取依赖 LLM
- 向量库为本地 FAISS
'@
'backend/app/config.py' = @'
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
PARSED_DIR = DATA_DIR / "parsed"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"

class Settings(BaseSettings):
    app_name: str = "LangChain Knowledge Base + Tender Parser MVP"
    app_version: str = "0.1.0"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    temperature: float = 0.0
    top_k: int = 4
    chunk_size: int = 800
    chunk_overlap: int = 100
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
for path in [DATA_DIR, UPLOAD_DIR, PARSED_DIR, VECTORSTORE_DIR]:
    path.mkdir(parents=True, exist_ok=True)
'@
'backend/app/main.py' = @'
from fastapi import FastAPI
from backend.app.api.knowledge_base import router as kb_router
from backend.app.api.tender_parser import router as tender_router
from backend.app.schemas.common import ApiResponse
from backend.app.config import settings

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.include_router(kb_router, prefix="/api/kb", tags=["Knowledge Base"])
app.include_router(tender_router, prefix="/api/tender", tags=["Tender Parser"])

@app.get("/health", response_model=ApiResponse)
def health_check():
    return ApiResponse(success=True, message="服务正常", data={"status": "ok"})
'@
'backend/app/api/knowledge_base.py' = @'
from fastapi import APIRouter, File, HTTPException, UploadFile
from backend.app.config import UPLOAD_DIR
from backend.app.schemas.common import ApiResponse
from backend.app.schemas.knowledge_base import BuildKnowledgeBaseRequest, AskRequest
from backend.app.loaders.document_loader import load_document_text
from backend.app.services.text_splitter_service import split_documents
from backend.app.services.vector_store_service import build_and_save_vectorstore
from backend.app.rag.qa_service import answer_question

router = APIRouter()
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

@router.post("/upload", response_model=ApiResponse)
async def upload_document(file: UploadFile = File(...)):
    suffix = ""
    if file.filename and "." in file.filename:
        suffix = "." + file.filename.split(".")[-1].lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="仅支持 pdf、docx、txt 文件")

    save_path = UPLOAD_DIR / file.filename
    content = await file.read()
    save_path.write_bytes(content)
    return ApiResponse(success=True, message="文件上传成功", data={"file_name": file.filename, "saved_path": str(save_path)})

@router.post("/build", response_model=ApiResponse)
def build_knowledge_base(request: BuildKnowledgeBaseRequest):
    file_paths = []
    if request.file_names:
        for name in request.file_names:
            path = UPLOAD_DIR / name
            if not path.exists():
                raise HTTPException(status_code=404, detail=f"文件不存在: {name}")
            file_paths.append(path)
    else:
        file_paths = [p for p in UPLOAD_DIR.iterdir() if p.suffix.lower() in ALLOWED_EXTENSIONS]

    if not file_paths:
        raise HTTPException(status_code=400, detail="没有可用于构建知识库的文件")

    docs = []
    for path in file_paths:
        text = load_document_text(path)
        if text.strip():
            docs.append({"text": text, "source": path.name})

    if not docs:
        raise HTTPException(status_code=400, detail="文件内容为空，无法构建知识库")

    split_docs = split_documents(docs)
    result = build_and_save_vectorstore(split_docs)
    return ApiResponse(success=True, message="知识库构建成功", data=result)

@router.post("/ask", response_model=ApiResponse)
def ask_knowledge_base(request: AskRequest):
    result = answer_question(question=request.question, top_k=request.top_k)
    return ApiResponse(success=True, message="问答成功", data=result)
'@
'backend/app/api/tender_parser.py' = @'
from fastapi import APIRouter, File, HTTPException, UploadFile
from backend.app.config import UPLOAD_DIR
from backend.app.schemas.common import ApiResponse
from backend.app.parsers.tender_parser import parse_tender_file

router = APIRouter()
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

@router.post("/parse", response_model=ApiResponse)
async def parse_tender(file: UploadFile = File(...)):
    suffix = ""
    if file.filename and "." in file.filename:
        suffix = "." + file.filename.split(".")[-1].lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="仅支持 pdf、docx、txt 文件")

    save_path = UPLOAD_DIR / file.filename
    content = await file.read()
    save_path.write_bytes(content)
    result = parse_tender_file(save_path)
    return ApiResponse(success=True, message="标书解析成功", data=result)
'@
'backend/app/loaders/document_loader.py' = @'
from pathlib import Path
from docx import Document
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".txt", ".docx", ".pdf"}

def load_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def load_docx(path: Path) -> str:
    doc = Document(str(path))
    return "\n".join([p.text for p in doc.paragraphs if p.text and p.text.strip()])

def load_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    texts = []
    for page in reader.pages:
        texts.append(page.extract_text() or "")
    return "\n".join(texts)

def load_document_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"不支持的文件类型: {suffix}")
    if suffix == ".txt":
        return load_txt(path)
    if suffix == ".docx":
        return load_docx(path)
    if suffix == ".pdf":
        return load_pdf(path)
    raise ValueError(f"不支持的文件类型: {suffix}")
'@
'backend/app/services/text_splitter_service.py' = @'
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from backend.app.config import settings

def split_documents(raw_docs: list[dict]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", "。", "；", ";", " "]
    )
    final_docs = []
    for item in raw_docs:
        chunks = splitter.split_text(item["text"])
        for index, chunk in enumerate(chunks):
            final_docs.append(Document(page_content=chunk, metadata={"source": item["source"], "chunk_index": index}))
    return final_docs
'@
'backend/app/services/embedding_service.py' = @'
from langchain_openai import OpenAIEmbeddings
from backend.app.config import settings

def get_embeddings() -> OpenAIEmbeddings:
    if not settings.openai_api_key:
        raise ValueError("未配置 OPENAI_API_KEY")
    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )
'@
'backend/app/services/vector_store_service.py' = @'
from pathlib import Path
from langchain_community.vectorstores import FAISS
from backend.app.config import VECTORSTORE_DIR
from backend.app.services.embedding_service import get_embeddings

INDEX_PATH = VECTORSTORE_DIR / "kb_index"

def build_and_save_vectorstore(documents: list):
    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(documents, embeddings)
    vectorstore.save_local(str(INDEX_PATH))
    unique_sources = sorted({doc.metadata.get("source", "") for doc in documents})
    return {
        "document_count": len(documents),
        "sources": unique_sources,
        "vectorstore_path": str(INDEX_PATH)
    }

def load_vectorstore() -> FAISS:
    if not Path(str(INDEX_PATH)).exists():
        raise FileNotFoundError("向量库不存在，请先构建知识库")
    embeddings = get_embeddings()
    return FAISS.load_local(str(INDEX_PATH), embeddings, allow_dangerous_deserialization=True)

def search_similar_chunks(query: str, top_k: int):
    vectorstore = load_vectorstore()
    return vectorstore.similarity_search_with_score(query, k=top_k)
'@
'backend/app/services/llm_client.py' = @'
from langchain_openai import ChatOpenAI
from backend.app.config import settings

def get_chat_model() -> ChatOpenAI:
    if not settings.openai_api_key:
        raise ValueError("未配置 OPENAI_API_KEY")
    return ChatOpenAI(
        model=settings.openai_chat_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=settings.temperature,
    )

def invoke_llm(prompt: str) -> str:
    model = get_chat_model()
    response = model.invoke(prompt)
    return response.content if hasattr(response, "content") else str(response)
'@
'backend/app/rag/qa_service.py' = @'
from backend.app.config import settings
from backend.app.services.llm_client import invoke_llm
from backend.app.services.vector_store_service import search_similar_chunks

QA_PROMPT_TEMPLATE = """你是一个公司内部知识库问答助手。
请严格基于给定上下文回答问题，不要编造。
如果上下文中没有明确答案，请直接回答“知识库中没有足够信息”。

问题：{question}

上下文：
{context}

请给出简洁、准确的中文回答。
"""

def answer_question(question: str, top_k: int | None = None) -> dict:
    k = top_k or settings.top_k
    results = search_similar_chunks(question, k)
    if not results:
        return {"answer": "知识库中没有足够信息", "sources": [], "chunks": [], "score": []}

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
        context_parts.append(f"来源：{source}\n内容：{chunk_text}")

    prompt = QA_PROMPT_TEMPLATE.format(question=question, context="\n\n".join(context_parts))
    answer = invoke_llm(prompt)
    return {
        "answer": answer,
        "sources": list(dict.fromkeys(sources)),
        "chunks": chunks,
        "score": scores,
    }
'@
'backend/app/parsers/tender_parser.py' = @'
import json
import re
from pathlib import Path
from backend.app.config import PARSED_DIR
from backend.app.loaders.document_loader import load_document_text
from backend.app.prompts.tender_extract_prompt import build_tender_extract_prompt
from backend.app.services.llm_client import invoke_llm

SECTION_PATTERN = re.compile(
    r"(?m)^(第[一二三四五六七八九十百0-9]+章[^\n]{0,80}|第[一二三四五六七八九十百0-9]+节[^\n]{0,80}|[0-9]+\.[0-9A-Za-z\.、\s]{0,80}|[一二三四五六七八九十]+、[^\n]{0,80})$"
)

def split_sections(text: str) -> list[dict]:
    matches = list(SECTION_PATTERN.finditer(text))
    if not matches:
        return [{"title": "全文", "content": text[:3000] if text else ""}]

    sections = []
    for index, match in enumerate(matches):
        title = match.group(0).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if content:
            sections.append({"title": title, "content": content})

    return sections or [{"title": "全文", "content": text[:3000]}]

def normalize_json_text(raw_text: str) -> str:
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```json", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"^```", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned

def extract_fields_with_llm(file_name: str, text: str, sections: list[dict]) -> dict:
    prompt = build_tender_extract_prompt(file_name=file_name, full_text=text[:20000], sections=sections[:20])
    raw_result = invoke_llm(prompt)
    json_text = normalize_json_text(raw_result)
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        data = {
            "file_name": file_name,
            "project_name": "",
            "tender_company": "",
            "deadline": "",
            "qualification_requirements": [],
            "technical_requirements": [],
            "business_requirements": [],
            "scoring_rules": [],
            "sections": sections,
            "raw_llm_output": raw_result,
        }
    data["file_name"] = file_name
    data["sections"] = sections
    return data

def parse_tender_file(path: Path) -> dict:
    text = load_document_text(path)
    sections = split_sections(text)
    result = extract_fields_with_llm(file_name=path.name, text=text, sections=sections)
    output_path = PARSED_DIR / f"{path.stem}.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
'@
'backend/app/prompts/tender_extract_prompt.py' = @'
import json

def build_tender_extract_prompt(file_name: str, full_text: str, sections: list[dict]) -> str:
    sections_text = json.dumps(sections, ensure_ascii=False, indent=2)
    return f"""你是一个招标文件解析助手。
请根据给定的招标文件内容，提取关键信息，并严格返回 JSON。
不要输出解释，不要输出 markdown 代码块，不要补充多余文字。

必须返回如下结构：
{{
  \"file_name\": \"{file_name}\",
  \"project_name\": \"\",
  \"tender_company\": \"\",
  \"deadline\": \"\",
  \"qualification_requirements\": [],
  \"technical_requirements\": [],
  \"business_requirements\": [],
  \"scoring_rules\": [],
  \"sections\": []
}}

字段要求：
- project_name：项目名称
- tender_company：招标单位
- deadline：投标截止时间，没有就留空字符串
- qualification_requirements：资质要求，提取为字符串数组
- technical_requirements：技术要求，提取为字符串数组
- business_requirements：商务要求，提取为字符串数组
- scoring_rules：评分办法，提取为字符串数组
- sections：保持空数组即可，最终由程序写回

如果某字段无法确定，请使用空字符串或空数组，不要编造。

文件名：{file_name}

章节信息：
{sections_text}

全文（可能被截断）：
{full_text}
"""
'@
'backend/app/schemas/common.py' = @'
from typing import Any
from pydantic import BaseModel

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Any | None = None
'@
'backend/app/schemas/knowledge_base.py' = @'
from pydantic import BaseModel, Field

class BuildKnowledgeBaseRequest(BaseModel):
    file_names: list[str] | None = Field(default=None, description="要构建知识库的文件名列表")

class AskRequest(BaseModel):
    question: str = Field(..., description="用户问题")
    top_k: int | None = Field(default=None, description="检索片段数量")

class AskResponseData(BaseModel):
    answer: str
    sources: list[str]
    chunks: list[str]
    score: list[float]
'@
'backend/app/schemas/tender_parser.py' = @'
from pydantic import BaseModel, Field

class TenderSection(BaseModel):
    title: str
    content: str

class TenderParseResponseData(BaseModel):
    file_name: str
    project_name: str = ""
    tender_company: str = ""
    deadline: str = ""
    qualification_requirements: list[str] = Field(default_factory=list)
    technical_requirements: list[str] = Field(default_factory=list)
    business_requirements: list[str] = Field(default_factory=list)
    scoring_rules: list[str] = Field(default_factory=list)
    sections: list[TenderSection] = Field(default_factory=list)
'@
'backend/app/__init__.py' = ''
'backend/app/api/__init__.py' = ''
'backend/app/services/__init__.py' = ''
'backend/app/loaders/__init__.py' = ''
'backend/app/rag/__init__.py' = ''
'backend/app/parsers/__init__.py' = ''
'backend/app/prompts/__init__.py' = ''
'backend/app/schemas/__init__.py' = ''
}

foreach ($entry in $files.GetEnumerator()) {
    $path = Join-Path $base $entry.Key
    $dir = Split-Path $path -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    Set-Content -Path $path -Value $entry.Value -Encoding UTF8
}

Write-Output "Project files generated."
