"""HTTP 响应头变量提取。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx


def extract_header(response: httpx.Response, name: str) -> str:
    """从响应头中提取值。"""
    value = response.headers.get(name)
    assert value is not None, f"响应头不存在: {name}"
    return value


def extract_set_cookie(response: httpx.Response, cookie_name: str) -> str:
    """从 Set-Cookie 中提取指定 cookie 的值。"""
    value = response.cookies.get(cookie_name)
    assert value is not None, f"Cookie 不存在: {cookie_name}"
    return value
