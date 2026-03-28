"""HTTP 状态码断言。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import allure

if TYPE_CHECKING:
    import httpx


def validate_status(response: httpx.Response, expected: int) -> None:
    """断言响应状态码。"""
    with allure.step(f"断言状态码 == {expected}"):
        actual = response.status_code
        assert actual == expected, f"状态码不匹配：期望 {expected}，实际 {actual}\n响应体: {response.text[:500]}"


def validate_success(response: httpx.Response) -> None:
    """断言响应为成功状态（2xx）。"""
    with allure.step("断言响应成功 (2xx)"):
        assert 200 <= response.status_code < 300, f"响应非成功状态: {response.status_code}"


def validate_error(response: httpx.Response, expected_status: int, error_field: str = "message") -> None:
    """断言错误响应。"""
    validate_status(response, expected_status)
    body: dict[str, Any] = response.json()
    assert error_field in body, f"错误响应缺少 {error_field} 字段"
