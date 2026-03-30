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
        raise HTTPException(status_code=400, detail="浠呮敮鎸?pdf銆乨ocx銆乼xt 鏂囦欢")

    save_path = UPLOAD_DIR / file.filename
    content = await file.read()
    save_path.write_bytes(content)
    result = parse_tender_file(save_path)
    return ApiResponse(success=True, message="鏍囦功瑙ｆ瀽鎴愬姛", data=result)
