from pydantic import BaseModel, Field

class BuildKnowledgeBaseRequest(BaseModel):
    file_names: list[str] | None = Field(default=None, description="瑕佹瀯寤虹煡璇嗗簱鐨勬枃浠跺悕鍒楄〃")

class AskRequest(BaseModel):
    question: str = Field(..., description="鐢ㄦ埛闂")
    top_k: int | None = Field(default=None, description="妫€绱㈢墖娈垫暟閲?)

class AskResponseData(BaseModel):
    answer: str
    sources: list[str]
    chunks: list[str]
    score: list[float]
