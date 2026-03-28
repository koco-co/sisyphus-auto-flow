"""断言模型定义。"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class AssertionType(StrEnum):
    """断言类型枚举。"""

    STATUS_CODE = "status_code"
    JSON_FIELD = "json_field"
    JSON_MATCH = "json_match"
    JSON_LENGTH = "json_length"
    JSON_CONTAINS = "json_contains"
    DB_RECORD = "db_record"
    DB_FIELD = "db_field"
    DB_COUNT = "db_count"
    RESPONSE_TIME = "response_time"
    HEADER = "header"


class AssertionConfig(BaseModel):
    """断言配置。"""

    type: AssertionType = Field(description="断言类型")
    target: str = Field(description="断言目标（JSONPath、SQL 等）")
    expected: str | int | float | bool | None = Field(default=None, description="期望值")
    comparator: str = Field(default="eq", description="比较器（eq, ne, gt, lt, contains, exists, regex）")
    description: str = Field(default="", description="断言描述")
