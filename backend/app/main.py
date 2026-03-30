from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.knowledge_base import router as kb_router
from backend.app.api.tender_parser import router as tender_router
from backend.app.config import settings
from backend.app.schemas.common import ApiResponse

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(kb_router, prefix="/api/kb", tags=["Knowledge Base"])
app.include_router(tender_router, prefix="/api/tender", tags=["Tender Parser"])


@app.get("/health", response_model=ApiResponse)
def health_check():
    return ApiResponse(success=True, message="Service is healthy", data={"status": "ok"})
