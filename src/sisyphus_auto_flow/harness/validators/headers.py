"""响应头断言。"""

from __future__ import annotations

from typing import TYPE_CHECKING

import allure

if TYPE_CHECKING:
    import httpx


def validate_header(response: httpx.Response, name: str, expected: str) -> None:
    """断言响应头的值。"""
    with allure.step(f"断言响应头 {name} == {expected}"):
        actual = response.headers.get(name)
        assert actual is not None, f"响应头不存在: {name}"
        assert actual == expected, f"响应头不匹配: {name}，期望 {expected}，实际 {actual}"


def validate_content_type(response: httpx.Response, expected: str = "application/json") -> None:
    """断言 Content-Type。"""
    with allure.step(f"断言 Content-Type 包含 {expected}"):
        ct = response.headers.get("content-type", "")
        assert expected in ct, f"Content-Type 不匹配: 期望包含 {expected}，实际 {ct}"


def validate_cors_headers(response: httpx.Response) -> None:
    """断言 CORS 相关响应头存在。"""
    with allure.step("断言 CORS 响应头"):
        assert response.headers.get("access-control-allow-origin") is not None, "缺少 Access-Control-Allow-Origin"
