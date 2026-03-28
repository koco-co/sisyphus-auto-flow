"""测试链路可观测性支持。"""

from __future__ import annotations

import json
import uuid
from typing import Any

import allure


def build_trace_context() -> dict[str, str]:
    """构建最小 trace 上下文。"""
    trace_id = uuid.uuid4().hex
    span_id = uuid.uuid4().hex[:16]
    return {
        "trace_id": trace_id,
        "span_id": span_id,
        "traceparent": f"00-{trace_id}-{span_id}-01",
    }


def attach_trace_metadata(
    *,
    method: str,
    url: str,
    status_code: int,
    duration_ms: float,
    trace_context: dict[str, str],
) -> None:
    """将 trace 元数据附着到测试输出。"""
    payload: dict[str, Any] = {
        "trace_id": trace_context["trace_id"],
        "span_id": trace_context["span_id"],
        "traceparent": trace_context["traceparent"],
        "method": method,
        "url": url,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
    }
    allure.attach(
        json.dumps(payload, ensure_ascii=False, indent=2),
        name="可观测性元数据",
        attachment_type=allure.attachment_type.JSON,
    )
