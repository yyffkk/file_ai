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
    return ApiResponse(success=True, message="鏈嶅姟姝ｅ父", data={"status": "ok"})
