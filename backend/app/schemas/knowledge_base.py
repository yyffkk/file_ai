"""知识库相关请求/响应模型。"""

from pydantic import BaseModel, Field


class CreateKnowledgeBaseRequest(BaseModel):
    """创建知识库时需要的字段。"""

    name: str = Field(..., min_length=1, description="Knowledge base display name")


class BuildKnowledgeBaseRequest(BaseModel):
    """构建向量库时的入参。"""

    knowledge_base_id: str = Field(..., description="Knowledge base identifier")
    file_names: list[str] | None = Field(default=None, description="File names to build into the knowledge base")


class PreviewKnowledgeBaseRequest(BaseModel):
    """预览 SQL 识别与切块结果。"""

    knowledge_base_id: str = Field(..., description="Knowledge base identifier")
    file_names: list[str] | None = Field(default=None, description="Optional file names to preview")


class AskRequest(BaseModel):
    """知识库问答请求。"""

    knowledge_base_id: str = Field(..., description="Knowledge base identifier")
    question: str = Field(..., description="User question")
    top_k: int | None = Field(default=None, description="Number of retrieved chunks")


class AskResponseData(BaseModel):
    """问答接口 data 字段的结构。"""

    answer: str
    sources: list[str]
    chunks: list[str]
    score: list[float]
