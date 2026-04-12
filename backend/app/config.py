"""项目基础配置。"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DOCUMENTS_DIR = DATA_DIR / "documents"
PARSED_DIR = DATA_DIR / "parsed"
GENERATED_DIR = DATA_DIR / "generated"
QDRANT_DIR = DATA_DIR / "qdrant"


class Settings(BaseSettings):
    """应用运行时配置。"""

    app_name: str = "Knowledge Base QA MVP"
    app_version: str = "0.3.0"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_chat_model: str = "gpt-4o-mini"
    temperature: float = 0.0
    top_k: int = 4
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    qdrant_path: Path = QDRANT_DIR
    embedding_model_name: str = "BAAI/bge-small-zh-v1.5"
    sql_summary_use_llm: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

for path in [DATA_DIR, UPLOAD_DIR, DOCUMENTS_DIR, PARSED_DIR, GENERATED_DIR, QDRANT_DIR]:
    path.mkdir(parents=True, exist_ok=True)
