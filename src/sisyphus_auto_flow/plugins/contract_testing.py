"""轻量 contract testing 支持。"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from typing import Any


def schemathesis_available() -> bool:
    """返回是否安装了 schemathesis。"""
    return importlib.util.find_spec("schemathesis") is not None


@dataclass(frozen=True)
class ContractValidator:
    """轻量响应契约校验器。"""

    enabled: bool = False

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> ContractValidator:
        """从配置构建校验器。"""
        harness_cfg = config.get("harness", {})
        contract_cfg = harness_cfg.get("contract", {})
        return cls(enabled=bool(contract_cfg.get("enabled", False)))

    def validate_response(self, payload: dict[str, Any], schema: dict[str, Any]) -> None:
        """按最小 schema 子集校验响应体。"""
        if not self.enabled:
            return

        required_fields = schema.get("required", [])
        for field in required_fields:
            assert field in payload, f"缺少必填字段: {field}"

        properties = schema.get("properties", {})
        for field, field_schema in properties.items():
            if field not in payload:
                continue
            expected_type = field_schema.get("type")
            if expected_type is None:
                continue
            actual = payload[field]
            assert _matches_type(actual, expected_type), (
                f"字段类型不匹配: {field}, 期望 {expected_type}, 实际 {type(actual).__name__}"
            )


def _matches_type(value: Any, expected_type: str) -> bool:
    """判断值是否匹配简化 schema 类型。"""
    type_map: dict[str, type[Any]] = {
        "string": str,
        "integer": int,
        "number": (int, float),  # type: ignore[assignment]
        "boolean": bool,
        "object": dict,
        "array": list,
    }
    mapped = type_map.get(expected_type)
    if mapped is None:
        return True
    return isinstance(value, mapped)
