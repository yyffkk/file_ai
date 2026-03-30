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
        raise HTTPException(status_code=400, detail="浠呮敮鎸?pdf銆乨ocx銆乼xt 鏂囦欢")

    save_path = UPLOAD_DIR / file.filename
    content = await file.read()
    save_path.write_bytes(content)
    return ApiResponse(success=True, message="鏂囦欢涓婁紶鎴愬姛", data={"file_name": file.filename, "saved_path": str(save_path)})

@router.post("/build", response_model=ApiResponse)
def build_knowledge_base(request: BuildKnowledgeBaseRequest):
    file_paths = []
    if request.file_names:
        for name in request.file_names:
            path = UPLOAD_DIR / name
            if not path.exists():
                raise HTTPException(status_code=404, detail=f"鏂囦欢涓嶅瓨鍦? {name}")
            file_paths.append(path)
    else:
        file_paths = [p for p in UPLOAD_DIR.iterdir() if p.suffix.lower() in ALLOWED_EXTENSIONS]

    if not file_paths:
        raise HTTPException(status_code=400, detail="娌℃湁鍙敤浜庢瀯寤虹煡璇嗗簱鐨勬枃浠?)

    docs = []
    for path in file_paths:
        text = load_document_text(path)
        if text.strip():
            docs.append({"text": text, "source": path.name})

    if not docs:
        raise HTTPException(status_code=400, detail="鏂囦欢鍐呭涓虹┖锛屾棤娉曟瀯寤虹煡璇嗗簱")

    split_docs = split_documents(docs)
    result = build_and_save_vectorstore(split_docs)
    return ApiResponse(success=True, message="鐭ヨ瘑搴撴瀯寤烘垚鍔?, data=result)

@router.post("/ask", response_model=ApiResponse)
def ask_knowledge_base(request: AskRequest):
    result = answer_question(question=request.question, top_k=request.top_k)
    return ApiResponse(success=True, message="闂瓟鎴愬姛", data=result)
