"""JSON Schema 校验。

基于简单类型检查实现的轻量级 JSON Schema 验证，
支持两种模式：
1. 简易模式 — {"field": "type_name"} 平铺校验
2. 嵌套模式 — 类 JSON Schema 的递归校验
"""

from __future__ import annotations

from typing import Any

import allure
from loguru import logger

# 类型名称到 Python 类型的映射
_TYPE_MAP: dict[str, type | tuple[type, ...]] = {
    "str": str,
    "string": str,
    "int": int,
    "integer": int,
    "float": float,
    "number": (int, float),
    "bool": bool,
    "boolean": bool,
    "list": list,
    "array": list,
    "dict": dict,
    "object": dict,
    "null": type(None),
}


def validate_schema(body: dict[str, Any], schema: dict[str, Any]) -> None:
    """根据 Schema 校验 JSON 数据。

    支持两种 Schema 格式：
    - 简易格式: {"field_name": "type_name", ...}
    - 嵌套格式: {"type": "object", "required": [...], "properties": {...}}

    Args:
        body: 待校验的 JSON 数据
        schema: Schema 定义字典

    Raises:
        AssertionError: 校验失败时抛出
    """
    with allure.step(f"校验 JSON Schema ({len(schema)} 个规则)"):
        if "type" in schema and isinstance(schema.get("type"), str) and schema["type"] in _TYPE_MAP:
            # 嵌套模式
            errors = _validate_node(body, schema, path="$")
            assert not errors, "Schema 校验失败:\n" + "\n".join(f"  - {e}" for e in errors)
        else:
            # 简易模式：{"field_name": "type_name"}
            _validate_flat(body, schema)

    logger.debug("JSON Schema 校验通过")


def _validate_flat(body: dict[str, Any], schema: dict[str, Any]) -> None:
    """简易模式校验：字段名 → 类型名映射。"""
    for field, expected_type in schema.items():
        assert field in body, f"缺少字段: {field}"
        if expected_type == "any":
            continue
        py_type = _TYPE_MAP.get(expected_type)
        if py_type:
            assert isinstance(body[field], py_type), (
                f"字段 '{field}' 类型错误: 期望 {expected_type}，实际 {type(body[field]).__name__}"
            )


def _validate_node(data: Any, schema: dict[str, Any], path: str) -> list[str]:
    """递归校验单个节点。"""
    errors: list[str] = []

    # 校验类型
    expected_type = schema.get("type")
    if expected_type and isinstance(expected_type, str):
        py_type = _TYPE_MAP.get(expected_type)
        if py_type and not isinstance(data, py_type):
            errors.append(f"{path}: 期望类型 {expected_type}，实际 {type(data).__name__}")
            return errors

    # 校验对象的必需字段
    if isinstance(data, dict):
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                errors.append(f"{path}: 缺少必需字段 '{field}'")

        # 递归校验嵌套属性
        properties = schema.get("properties", {})
        for prop_name, prop_schema in properties.items():
            if prop_name in data:
                child_errors = _validate_node(data[prop_name], prop_schema, path=f"{path}.{prop_name}")
                errors.extend(child_errors)

    # 校验数组元素
    if isinstance(data, list):
        items_schema = schema.get("items")
        if items_schema:
            for i, item in enumerate(data):
                child_errors = _validate_node(item, items_schema, path=f"{path}[{i}]")
                errors.extend(child_errors)

    return errors
