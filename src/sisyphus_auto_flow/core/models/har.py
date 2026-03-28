"""HAR 文件数据模型。

基于 HTTP Archive 1.2 规范定义 Pydantic 模型，
用于类型安全地解析和校验 HAR 文件内容。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HarHeader(BaseModel):
    """HTTP 请求/响应头。"""

    name: str = Field(description="头名称")
    value: str = Field(description="头的值")


class HarQueryParam(BaseModel):
    """URL 查询参数。"""

    name: str = Field(description="参数名")
    value: str = Field(description="参数值")


class HarPostData(BaseModel):
    """POST 请求体。"""

    mime_type: str = Field(default="", alias="mimeType", description="MIME 类型")
    text: str = Field(default="", description="请求体文本")


class HarContent(BaseModel):
    """响应体内容。"""

    size: int = Field(default=0, description="内容大小（字节）")
    mime_type: str = Field(default="", alias="mimeType", description="MIME 类型")
    text: str = Field(default="", description="响应体文本")


class HarTimings(BaseModel):
    """请求耗时信息。"""

    send: float = Field(default=-1, description="发送耗时（毫秒）")
    wait: float = Field(default=-1, description="等待耗时（毫秒）")
    receive: float = Field(default=-1, description="接收耗时（毫秒）")


class HarRequest(BaseModel):
    """HTTP 请求信息。"""

    method: str = Field(description="HTTP 方法")
    url: str = Field(description="请求 URL")
    http_version: str = Field(default="HTTP/1.1", alias="httpVersion", description="HTTP 版本")
    headers: list[HarHeader] = Field(default_factory=list, description="请求头列表")
    query_string: list[HarQueryParam] = Field(default_factory=list, alias="queryString", description="查询参数")
    post_data: HarPostData | None = Field(default=None, alias="postData", description="POST 请求体")

    @property
    def headers_dict(self) -> dict[str, str]:
        """将请求头列表转换为字典。"""
        return {h.name: h.value for h in self.headers}

    @property
    def query_dict(self) -> dict[str, str]:
        """将查询参数列表转换为字典。"""
        return {q.name: q.value for q in self.query_string}


class HarResponse(BaseModel):
    """HTTP 响应信息。"""

    status: int = Field(description="HTTP 状态码")
    status_text: str = Field(default="", alias="statusText", description="状态文本")
    headers: list[HarHeader] = Field(default_factory=list, description="响应头列表")
    content: HarContent = Field(default_factory=HarContent, description="响应体内容")

    @property
    def headers_dict(self) -> dict[str, str]:
        """将响应头列表转换为字典。"""
        return {h.name: h.value for h in self.headers}


class HarEntry(BaseModel):
    """HAR 中的单个请求/响应条目。"""

    request: HarRequest = Field(description="请求信息")
    response: HarResponse = Field(description="响应信息")
    timings: HarTimings = Field(default_factory=HarTimings, description="耗时信息")
    started_date_time: str = Field(default="", alias="startedDateTime", description="请求开始时间")


class HarCreator(BaseModel):
    """HAR 文件创建者信息。"""

    name: str = Field(default="", description="创建工具名称")
    version: str = Field(default="", description="工具版本")


class HarLog(BaseModel):
    """HAR 日志主体。"""

    version: str = Field(default="1.2", description="HAR 规范版本")
    creator: HarCreator = Field(default_factory=HarCreator, description="创建者信息")
    entries: list[HarEntry] = Field(default_factory=list, description="请求条目列表")


class HarFile(BaseModel):
    """HAR 文件根模型。"""

    log: HarLog = Field(description="HAR 日志")


class NormalizedHarRequest(BaseModel):
    """归一化后的 HAR 请求信息。"""

    sequence: int = Field(description="请求顺序")
    method: str = Field(description="HTTP 方法")
    path: str = Field(description="请求路径")
    module: str | None = Field(default=None, description="归属业务模块")
    module_api_dir: str | None = Field(default=None, description="模块 API 目录")
    module_description: str | None = Field(default=None, description="模块描述")
    query_params: dict[str, str] | None = Field(default=None, description="查询参数")
    headers: dict[str, str] = Field(default_factory=dict, description="过滤后的请求头")
    body: dict[str, Any] | list[Any] | str | None = Field(default=None, description="请求体")
    response_status: int = Field(description="响应状态码")
    response_body: dict[str, Any] | list[Any] | str | None = Field(default=None, description="响应体")
    extracted_ids: list[str] | None = Field(default=None, description="从响应中提取出的 ID")
    depends_on: int | None = Field(default=None, description="依赖的前置请求序号")


class NormalizedHarResult(BaseModel):
    """归一化后的 HAR 解析结果。"""

    source: str = Field(description="源 HAR 文件名")
    total_entries: int = Field(description="HAR 原始请求数")
    filtered_entries: int = Field(description="过滤后的 API 请求数")
    requests: list[NormalizedHarRequest] = Field(default_factory=list, description="归一化请求列表")
