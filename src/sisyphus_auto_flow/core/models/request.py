"""HTTP 请求数据模型。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RequestConfig(BaseModel):
    """测试请求配置。"""

    method: str = Field(default="GET", description="HTTP 方法")
    url: str = Field(description="请求路径")
    headers: dict[str, str] = Field(default_factory=dict, description="请求头")
    params: dict[str, Any] = Field(default_factory=dict, description="查询参数")
    json_body: dict[str, Any] | None = Field(default=None, alias="json", description="JSON 请求体")
    data: dict[str, Any] | None = Field(default=None, description="表单数据")
    timeout: float = Field(default=30.0, description="超时时间（秒）")
    authenticated: bool = Field(default=True, description="是否携带认证信息")
