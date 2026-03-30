from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.app.config import UPLOAD_DIR
from backend.app.parsers.tender_parser import parse_tender_file
from backend.app.schemas.common import ApiResponse

router = APIRouter()
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


@router.post("/parse", response_model=ApiResponse)
async def parse_tender(file: UploadFile = File(...)):
    suffix = ""
    if file.filename and "." in file.filename:
        suffix = "." + file.filename.split(".")[-1].lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only pdf, docx and txt files are supported")

    save_path = UPLOAD_DIR / file.filename
    content = await file.read()
    save_path.write_bytes(content)

    result = parse_tender_file(save_path)
    return ApiResponse(success=True, message="Tender parsed successfully", data=result)
