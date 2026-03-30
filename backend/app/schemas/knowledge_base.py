from pydantic import BaseModel, Field


class BuildKnowledgeBaseRequest(BaseModel):
    file_names: list[str] | None = Field(default=None, description="File names to build into the knowledge base")


class AskRequest(BaseModel):
    question: str = Field(..., description="User question")
    top_k: int | None = Field(default=None, description="Number of retrieved chunks")


class AskResponseData(BaseModel):
    answer: str
    sources: list[str]
    chunks: list[str]
    score: list[float]
