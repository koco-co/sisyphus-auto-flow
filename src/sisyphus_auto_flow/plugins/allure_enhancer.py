"""Allure 报告增强插件。

自动将请求和响应信息附加到 Allure 报告步骤中。
"""

from __future__ import annotations

import json
from typing import Any

import allure


def attach_request(method: str, url: str, body: Any = None, headers: dict[str, str] | None = None) -> None:
    """将请求信息附加到 Allure 报告。"""
    info: dict[str, Any] = {"method": method, "url": url}
    if headers:
        info["headers"] = headers
    if body:
        info["body"] = body

    allure.attach(
        json.dumps(info, ensure_ascii=False, indent=2),
        name="请求信息",
        attachment_type=allure.attachment_type.JSON,
    )


def attach_response(status: int, body: Any = None, duration_ms: float = 0) -> None:
    """将响应信息附加到 Allure 报告。"""
    info: dict[str, Any] = {"status": status, "duration_ms": round(duration_ms)}
    if body:
        info["body"] = body

    allure.attach(
        json.dumps(info, ensure_ascii=False, indent=2),
        name="响应信息",
        attachment_type=allure.attachment_type.JSON,
    )
