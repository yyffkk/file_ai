"""AI 写标书相关模型。"""

from pydantic import BaseModel, Field


class GenerateTenderRequest(BaseModel):
    project_name: str = Field(..., min_length=1, description="项目名称")
    requirement_text: str = Field(default="", description="招标需求文本")
    knowledge_base_id: str = Field(..., min_length=1, description="资料库/知识库 ID")
    top_k: int | None = Field(default=6, description="检索片段数量")


class SaveTenderDraftRequest(BaseModel):
    project_name: str = Field(..., min_length=1, description="项目名称")
    content: str = Field(..., min_length=1, description="生成内容")
    knowledge_base_id: str = Field(..., min_length=1, description="资料库/知识库 ID")
