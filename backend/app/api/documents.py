"""统一文档中心 API。"""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.app.parsers.tender_parser import parse_tender_file
from backend.app.schemas.common import ApiResponse
from backend.app.services.document_center_service import (
    attach_document_to_kb,
    create_document_record,
    get_document,
    get_parse_result,
    list_documents,
    mark_parse_completed,
    mark_parse_failed,
    mark_parse_processing,
    save_document_content,
)

router = APIRouter()


@router.get("", response_model=ApiResponse)
def get_documents():
    return ApiResponse(success=True, message="Documents fetched successfully", data=list_documents())


@router.post("/upload", response_model=ApiResponse)
async def upload_document(
    file: UploadFile = File(...),
    knowledge_base_id: str = Form(default=""),
    enable_kb: bool = Form(default=False),
    enable_parse: bool = Form(default=False),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required")

    if not enable_kb and not enable_parse:
        raise HTTPException(status_code=400, detail="At least one processing target must be selected")

    if enable_kb and not knowledge_base_id:
        raise HTTPException(status_code=400, detail="knowledge_base_id is required when enable_kb is true")

    content = await file.read()
    item = create_document_record(
        file_name=file.filename,
        size=len(content),
        enable_kb=enable_kb,
        enable_parse=enable_parse,
        knowledge_base_id=knowledge_base_id or None,
    )
    item = save_document_content(item["id"], content)

    if enable_kb and knowledge_base_id:
        item = attach_document_to_kb(item["id"], knowledge_base_id)

    if enable_parse:
        try:
            mark_parse_processing(item["id"])
            result = parse_tender_file(item_path(item["id"]))
            parse_path = parse_result_path(item["name"])
            item = mark_parse_completed(item["id"], str(parse_path))
        except Exception as exc:
            item = mark_parse_failed(item["id"], str(exc))
            raise HTTPException(status_code=500, detail=f"Tender parse failed: {exc}") from exc
        return ApiResponse(success=True, message="Document uploaded and processed successfully", data={"document": item, "parse_result": result})

    return ApiResponse(success=True, message="Document uploaded successfully", data={"document": get_document(item["id"])})


@router.get("/{document_id}", response_model=ApiResponse)
def get_document_detail(document_id: str):
    return ApiResponse(success=True, message="Document fetched successfully", data=get_document(document_id))


@router.get("/{document_id}/parse-result", response_model=ApiResponse)
def get_document_parse_result(document_id: str):
    return ApiResponse(success=True, message="Parse result fetched successfully", data=get_parse_result(document_id))



def item_path(document_id: str):
    from pathlib import Path

    item = get_document(document_id)
    return Path(item["path"])



def parse_result_path(file_name: str):
    from pathlib import Path

    from backend.app.config import PARSED_DIR

    return PARSED_DIR / f"{Path(file_name).stem}.json"
