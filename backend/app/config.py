from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
PARSED_DIR = DATA_DIR / "parsed"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"

class Settings(BaseSettings):
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
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
for path in [DATA_DIR, UPLOAD_DIR, PARSED_DIR, VECTORSTORE_DIR]:
    path.mkdir(parents=True, exist_ok=True)
