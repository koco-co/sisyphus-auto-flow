"""JSONPath 变量提取。"""

from __future__ import annotations

from typing import Any

from jsonpath_ng.ext import parse as jsonpath_parse


def extract_jsonpath(body: dict[str, Any] | list[Any], expr: str) -> Any:
    """从 JSON 数据中提取单个值。"""
    matches = jsonpath_parse(expr).find(body)
    assert len(matches) > 0, f"JSONPath 提取失败: {expr}"
    return matches[0].value


def extract_jsonpath_list(body: dict[str, Any] | list[Any], expr: str) -> list[Any]:
    """从 JSON 数据中提取所有匹配值。"""
    matches = jsonpath_parse(expr).find(body)
    return [m.value for m in matches]
