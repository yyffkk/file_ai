"""FastAPI 应用入口。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.documents import router as document_router
from backend.app.api.knowledge_base import router as kb_router
from backend.app.api.tender_parser import router as tender_router
from backend.app.config import settings
from backend.app.schemas.common import ApiResponse

# 应用实例：标题和版本来自统一配置，避免写死在多个地方。
app = FastAPI(title=settings.app_name, version=settings.app_version)

# MVP 阶段先放开 CORS，方便前后端本地分端口联调。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由注册。
app.include_router(document_router, prefix="/api/documents", tags=["Documents"])
app.include_router(kb_router, prefix="/api/kb", tags=["Knowledge Base"])
app.include_router(tender_router, prefix="/api/tender", tags=["Tender Parser"])


@app.get("/health", response_model=ApiResponse)
def health_check():
    """健康检查接口，供前端或运维探活。"""

    return ApiResponse(success=True, message="Service is healthy", data={"status": "ok"})
