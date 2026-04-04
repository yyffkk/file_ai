"""通用响应模型。"""

from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    """统一接口返回结构。"""

    success: bool
    message: str
    data: Any | None = None
