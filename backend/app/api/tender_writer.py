"""AI 写标书 API。"""

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.app.config import DOCUMENTS_DIR
from backend.app.loaders.document_loader import load_document_text
from backend.app.schemas.common import ApiResponse
from backend.app.schemas.tender_writer import GenerateTenderRequest, SaveTenderDraftRequest
from backend.app.services.knowledge_base_service import ensure_safe_filename, validate_extension
from backend.app.services.tender_writer_service import (
    generate_tender_draft,
    get_generated_result,
    list_generated_results,
    save_generated_result,
)

router = APIRouter()


@router.post("/requirement-upload", response_model=ApiResponse)
async def upload_requirement_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required")

    safe_name = ensure_safe_filename(file.filename)
    validate_extension(safe_name)
    stored_name = f"requirement_{uuid4().hex[:12]}_{safe_name}"
    path = DOCUMENTS_DIR / stored_name
    content = await file.read()
    path.write_bytes(content)

    try:
        text = load_document_text(Path(path))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Requirement file parse failed: {exc}") from exc

    return ApiResponse(
        success=True,
        message="Requirement file uploaded successfully",
        data={
            "file_name": safe_name,
            "stored_name": stored_name,
            "text": text[:30000],
        },
    )


@router.post("/generate", response_model=ApiResponse)
def generate_tender(request: GenerateTenderRequest):
    data = generate_tender_draft(
        project_name=request.project_name,
        requirement_text=request.requirement_text,
        knowledge_base_id=request.knowledge_base_id,
        top_k=request.top_k,
    )
    return ApiResponse(success=True, message="Tender draft generated successfully", data=data)


@router.get("/results", response_model=ApiResponse)
def get_results():
    return ApiResponse(success=True, message="Generated results fetched successfully", data=list_generated_results())


@router.post("/results", response_model=ApiResponse)
def save_result(request: SaveTenderDraftRequest):
    data = save_generated_result(
        project_name=request.project_name,
        content=request.content,
        knowledge_base_id=request.knowledge_base_id,
    )
    return ApiResponse(success=True, message="Generated result saved successfully", data=data)


@router.get("/results/{result_id}", response_model=ApiResponse)
def get_result_detail(result_id: str):
    try:
        data = get_generated_result(result_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ApiResponse(success=True, message="Generated result fetched successfully", data=data)
