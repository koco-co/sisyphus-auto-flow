"""数据库断言。"""

from __future__ import annotations

from typing import Any

import allure
from loguru import logger


def validate_db_record(
    cursor: Any,
    sql: str,
    params: list[Any] | tuple[Any, ...] | None = None,
    *,
    exists: bool = True,
) -> dict[str, Any] | None:
    """断言数据库记录是否存在。"""
    with allure.step(f"断言数据库记录{'存在' if exists else '不存在'}"):
        cursor.execute(sql, params)
        result = cursor.fetchone()
        if exists:
            assert result is not None, f"数据库记录不存在\nSQL: {sql}\n参数: {params}"
        else:
            assert result is None, f"数据库记录不应存在但存在\nSQL: {sql}"
        logger.debug(f"数据库断言通过: {sql}")
        return result


def validate_db_field(
    cursor: Any,
    sql: str,
    params: list[Any] | tuple[Any, ...] | None = None,
    *,
    field: str,
    expected: Any,
) -> None:
    """断言数据库字段值。"""
    with allure.step(f"断言数据库字段 {field} == {expected}"):
        cursor.execute(sql, params)
        result = cursor.fetchone()
        assert result is not None, f"数据库记录不存在\nSQL: {sql}"
        actual = result[field] if isinstance(result, dict) else result[0]
        assert actual == expected, f"数据库字段不匹配: {field}，期望 {expected}，实际 {actual}"


def validate_db_count(
    cursor: Any,
    sql: str,
    params: list[Any] | tuple[Any, ...] | None = None,
    *,
    expected: int,
) -> None:
    """断言数据库记录数量。"""
    with allure.step(f"断言数据库记录数 == {expected}"):
        cursor.execute(sql, params)
        result = cursor.fetchone()
        actual = result[0] if isinstance(result, tuple) else next(iter(result.values()))
        assert actual == expected, f"数据库记录数不匹配: 期望 {expected}，实际 {actual}"
