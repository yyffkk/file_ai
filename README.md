# LangChain Knowledge Base + Tender Parser MVP

A minimal runnable project with:

1. Knowledge base Q&A: upload files, split text, embed, store in FAISS, retrieve and answer
2. Tender parsing: upload PDF / DOCX / TXT files, extract text, split sections, extract structured JSON with LLM
3. Vue 3 frontend: simple interactive UI

## Tech Stack

### Backend
- Python 3.11
- FastAPI
- LangChain
- FAISS
- pypdf / python-docx
- local files + JSON

### Frontend
- Vue 3
- Vite
- Axios

## Project Structure

```text
langchain_tender_mvp/
├─ backend/
│  ├─ app/
│  └─ data/
├─ frontend/
├─ .env.example
├─ requirements.txt
└─ README.md
```

## Backend Start

```bash
cd D:\python_project\langchain_tender_mvp
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend URLs:
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/health

## Frontend Start

```bash
cd D:\python_project\langchain_tender_mvp\frontend
npm install
npm run dev
```

Frontend URL:
- http://127.0.0.1:5173

## Notes
- PDF support is text-based only, no OCR yet
- FAISS is local only
- This is an MVP, focused on running end to end first
