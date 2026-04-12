# SQL Semantic Knowledge Base MVP

一个面向 SQL 数据库逻辑检索的最小可运行项目，支持：

1. 上传 `.sql` / `.txt` / `.doc` / `.docx` / `.pdf`
2. 自动识别其中的 SQL 对象（存储过程、视图、触发器、表）
3. 按逻辑切块，而不是按长度切分
4. 为每个 chunk 生成语义 summary 和 retrieval_text
5. 使用 fastembed 生成向量
6. 存入 Qdrant 做语义检索
7. 用户通过自然语言查询数据库逻辑，再结合 raw SQL 返回解释

## Tech Stack

### Backend
- Python 3.11
- FastAPI
- qdrant-client
- fastembed
- langchain-openai
- pypdf / python-docx

### Frontend
- Vue 3
- Vite
- Axios

## Backend Start

```bash
cd D:\python_project\langchain_tender_mvp
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

## .env 示例

```env
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_CHAT_MODEL=gpt-4o-mini
TEMPERATURE=0
TOP_K=4
QDRANT_URL=
QDRANT_API_KEY=
EMBEDDING_MODEL_NAME=BAAI/bge-small-zh-v1.5
```

## 说明

- `QDRANT_URL` 留空时，默认使用本地 Qdrant 存储目录
- embedding 输入严格使用 retrieval_text，不直接使用 raw SQL
- `.txt/.doc/.docx/.pdf` 中只要包含 SQL 代码，也会尝试抽取 SQL 段并入库
- 当前逻辑切块重点增强了 `BEGIN...END`、多段 `IF/ELSE`、多个 `SELECT/UPDATE/INSERT/DELETE/MERGE`
