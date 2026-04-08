"""项目基础配置。

这里集中管理路径、模型参数和环境变量，方便前后端联调时快速定位配置来源。
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> backend 目录
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DOCUMENTS_DIR = DATA_DIR / "documents"
PARSED_DIR = DATA_DIR / "parsed"
GENERATED_DIR = DATA_DIR / "generated"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"


class Settings(BaseSettings):
    """应用运行时配置。

    默认值适合本地 MVP 运行；生产环境可通过 .env 覆盖。
    """

    app_name: str = "LangChain Knowledge Base + Tender Parser MVP"
    app_version: str = "0.1.0"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    temperature: float = 0.0
    top_k: int = 4
    chunk_size: int = 800
    chunk_overlap: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

# 应用启动时确保基础目录存在，避免上传、解析、建库时因目录缺失报错。
for path in [DATA_DIR, UPLOAD_DIR, DOCUMENTS_DIR, PARSED_DIR, GENERATED_DIR, VECTORSTORE_DIR]:
    path.mkdir(parents=True, exist_ok=True)
