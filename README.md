# LangChain 知识库 + 标书解析 MVP

这是一个可直接运行的最小项目，包含：

1. 知识库问答：上传文档、切分、向量化、FAISS 入库、检索问答
2. 标书解析：上传 PDF / DOCX / TXT 招标文件，提取文本、粗拆章节、调用 LLM 输出结构化 JSON
3. Vue 3 前端：提供最小可用交互页面

---

## 1. 技术栈

### 后端
- Python 3.11
- FastAPI
- LangChain
- FAISS（本地）
- pypdf / python-docx
- 本地文件 + JSON

### 前端
- Vue 3
- Vite
- Axios

---

## 2. 项目结构

```text
langchain_tender_mvp/
├─ backend/
│  ├─ app/
│  │  ├─ api/
│  │  │  ├─ knowledge_base.py
│  │  │  └─ tender_parser.py
│  │  ├─ loaders/
│  │  │  └─ document_loader.py
│  │  ├─ parsers/
│  │  │  └─ tender_parser.py
│  │  ├─ prompts/
│  │  │  └─ tender_extract_prompt.py
│  │  ├─ rag/
│  │  │  └─ qa_service.py
│  │  ├─ schemas/
│  │  │  ├─ common.py
│  │  │  ├─ knowledge_base.py
│  │  │  └─ tender_parser.py
│  │  ├─ services/
│  │  │  ├─ embedding_service.py
│  │  │  ├─ llm_client.py
│  │  │  ├─ text_splitter_service.py
│  │  │  └─ vector_store_service.py
│  │  ├─ config.py
│  │  └─ main.py
│  └─ data/
│     ├─ uploads/
│     ├─ parsed/
│     └─ vectorstore/
├─ frontend/
│  ├─ src/
│  │  ├─ App.vue
│  │  ├─ api.js
│  │  ├─ main.js
│  │  └─ style.css
│  ├─ index.html
│  ├─ package.json
│  └─ vite.config.js
├─ .env.example
├─ requirements.txt
└─ README.md
```

---

## 3. 后端启动

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

复制 `.env.example` 为 `.env`：

```env
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
TEMPERATURE=0
TOP_K=4
```

### 3.4 启动 FastAPI

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

启动后访问：
- Swagger：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/health>

---

## 4. 前端启动

先确保本机安装了 Node.js 18+。

```bash
cd D:\python_project\langchain_tender_mvp\frontend
npm install
npm run dev
```

启动后访问：
- 前端页面：<http://127.0.0.1:5173>

默认前端调用后端地址：
- `http://127.0.0.1:8000`

---

## 5. 前端功能

当前前端页面包含：

1. 知识库文档上传
2. 知识库构建
3. 知识库问答
4. 标书上传解析
5. 解析结果 JSON 展示
6. 问答命中片段和来源文件展示

---

## 6. 测试顺序

建议按这个顺序测试：

1. 启动后端
2. 启动前端
3. 上传知识库文档
4. 构建知识库
5. 输入问题做问答
6. 上传标书做解析
7. 检查 `backend/data/parsed/` 是否生成 JSON 文件

---

## 7. 当前边界

这是 MVP 版本，重点是先跑通：

- PDF 只支持文本型 PDF，不做 OCR
- 章节切分是规则粗拆分
- 字段抽取依赖 LLM 输出
- 向量库是本地 FAISS
- 前端是简洁版，不含登录、权限、多用户

---

## 8. 后续可扩展

后面你可以继续加：

- 登录和权限
- 文档列表页
- 多知识库管理
- OCR 扫描件识别
- SQLite 文档记录
- 标书解析结果对比/导出
- 页面美化和组件化
