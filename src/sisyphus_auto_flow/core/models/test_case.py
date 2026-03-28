"""测试用例数据模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field

from sisyphus_auto_flow.core.models.assertion import AssertionConfig  # noqa: TC001
from sisyphus_auto_flow.core.models.request import RequestConfig  # noqa: TC001


class TestStep(BaseModel):
    """单个测试步骤。"""

    name: str = Field(description="步骤名称")
    description: str = Field(default="", description="步骤描述")
    request: RequestConfig = Field(description="请求配置")
    assertions: list[AssertionConfig] = Field(default_factory=list, description="断言列表")
    extract: dict[str, str] = Field(default_factory=dict, description="变量提取（变量名 → JSONPath）")


class TestScenario(BaseModel):
    """测试场景（一个测试类）。"""

    name: str = Field(description="场景名称")
    description: str = Field(default="", description="场景描述")
    module: str = Field(description="所属模块")
    epic: str = Field(default="", description="Allure Epic")
    feature: str = Field(default="", description="Allure Feature")
    tags: list[str] = Field(default_factory=list, description="标签列表")
    pre_sql: list[str] = Field(default_factory=list, description="前置 SQL")
    steps: list[TestStep] = Field(default_factory=list, description="测试步骤列表")
