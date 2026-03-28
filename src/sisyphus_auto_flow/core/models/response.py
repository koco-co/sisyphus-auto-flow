"""HTTP 响应数据模型。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class JsonFieldAssertion(BaseModel):
    """JSON 字段断言。"""

    jsonpath: str = Field(description="JSONPath 表达式")
    expected: Any | None = Field(default=None, description="期望值")
    exists: bool | None = Field(default=None, description="是否存在")
    type_name: str | None = Field(default=None, description="期望类型名")
    pattern: str | None = Field(default=None, description="正则模式")


class ResponseValidation(BaseModel):
    """响应验证规则。"""

    status_code: int = Field(description="期望的状态码")
    json_fields: list[JsonFieldAssertion] = Field(default_factory=list, description="JSON 字段断言列表")
    response_time_ms: float | None = Field(default=None, description="最大响应时间（毫秒）")
