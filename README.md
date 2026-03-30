# LangChain 鐭ヨ瘑搴?+ 鏍囦功瑙ｆ瀽 MVP

杩欐槸涓€涓彲鐩存帴杩愯鐨勬渶灏忛」鐩紝鍖呭惈涓ゅ潡鑳藉姏锛?
1. **鐭ヨ瘑搴撻棶绛?*锛氫笂浼犳枃妗ｃ€佸垏鍒嗐€佸悜閲忓寲銆丗AISS 鍏ュ簱銆佹绱㈤棶绛?2. **鏍囦功瑙ｆ瀽**锛氫笂浼?PDF / DOCX / TXT 鎷涙爣鏂囦欢锛屾彁鍙栨枃鏈€佺矖鎷嗙珷鑺傘€佽皟鐢?LLM 杈撳嚭缁撴瀯鍖?JSON

## 1. 鎶€鏈爤
- Python 3.11
- FastAPI
- LangChain
- FAISS锛堟湰鍦帮級
- pypdf / python-docx
- 鏈湴鏂囦欢 + JSON

## 2. 椤圭洰缁撴瀯
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

## 3. 蹇€熷惎鍔?### 3.1 鍒涘缓铏氭嫙鐜
```bash
cd D:\python_project\langchain_tender_mvp
python -m venv .venv
.venv\Scripts\activate
```

### 3.2 瀹夎渚濊禆
```bash
pip install -r requirements.txt
```

### 3.3 閰嶇疆鐜鍙橀噺
澶嶅埗 `.env.example` 涓?`.env`锛岃嚦灏戦厤缃細
```env
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
TEMPERATURE=0
TOP_K=4
```

### 3.4 鍚姩鏈嶅姟
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

鍚姩鍚庢墦寮€锛?- Swagger: <http://127.0.0.1:8000/docs>
- 鍋ュ悍妫€鏌? <http://127.0.0.1:8000/health>

## 4. 娴嬭瘯椤哄簭
1. `/api/kb/upload` 涓婁紶鏂囨。
2. `/api/kb/build` 鏋勫缓鐭ヨ瘑搴?3. `/api/kb/ask` 鍋氶棶绛?4. `/api/tender/parse` 瑙ｆ瀽鏍囦功
5. 妫€鏌?`backend/data/parsed/` 杈撳嚭 JSON

## 5. 褰撳墠杈圭晫
- PDF 浠呮敮鎸佹枃鏈瀷 PDF锛屼笉鍋?OCR
- 绔犺妭鍒囧垎涓鸿鍒欑矖鎷嗗垎
- 瀛楁鎶藉彇渚濊禆 LLM
- 鍚戦噺搴撲负鏈湴 FAISS
