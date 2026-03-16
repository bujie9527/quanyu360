"""统一内容结构定义。"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic import Field


class ContentItem(BaseModel):
    """统一内容结构。"""

    title: str = Field(default="", description="标题")
    content: str = Field(default="", description="正文内容")
    tags: list[str] = Field(default_factory=list, description="标签列表")

    def model_dump_unified(self) -> dict[str, Any]:
        """返回标准 JSON 结构。"""
        return {
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
        }
