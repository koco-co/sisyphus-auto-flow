"""JSON 响应体断言。"""

from __future__ import annotations

from typing import Any

import allure
from jsonpath_ng.ext import parse as jsonpath_parse


def validate_json_field(body: dict[str, Any], jsonpath_expr: str, expected: Any) -> None:
    """断言 JSON 字段值。"""
    with allure.step(f"断言 {jsonpath_expr} == {expected}"):
        matches = jsonpath_parse(jsonpath_expr).find(body)
        assert len(matches) > 0, f"字段不存在: {jsonpath_expr}"
        actual = matches[0].value
        assert actual == expected, f"字段值不匹配: {jsonpath_expr}，期望 {expected}，实际 {actual}"


def validate_json_structure(body: dict[str, Any], required_fields: list[str]) -> None:
    """断言 JSON 包含所有必填字段。"""
    with allure.step(f"断言必填字段: {required_fields}"):
        for field in required_fields:
            matches = jsonpath_parse(field).find(body)
            assert len(matches) > 0, f"缺少必填字段: {field}"


def validate_json_not_empty(body: dict[str, Any], jsonpath_expr: str) -> None:
    """断言 JSON 字段非空。"""
    with allure.step(f"断言 {jsonpath_expr} 非空"):
        matches = jsonpath_parse(jsonpath_expr).find(body)
        assert len(matches) > 0, f"字段不存在: {jsonpath_expr}"
        value = matches[0].value
        assert value is not None and value != "" and value != [], f"字段为空: {jsonpath_expr}"
