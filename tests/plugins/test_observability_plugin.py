"""Observability plugin tests."""

from __future__ import annotations

import json


def test_observability_attaches_trace_metadata(monkeypatch) -> None:
    """Observability metadata should include trace IDs and request/response details."""
    from sisyphus_auto_flow.plugins import observability

    captured: list[tuple[dict[str, object], str]] = []

    def _attach(body: str, *, name: str, attachment_type) -> None:
        captured.append((json.loads(body), name))

    monkeypatch.setattr(observability.allure, "attach", _attach)

    trace = observability.build_trace_context()
    observability.attach_trace_metadata(
        method="POST",
        url="/health",
        status_code=201,
        duration_ms=12.5,
        trace_context=trace,
    )

    assert captured
    payload, name = captured[0]
    assert name == "可观测性元数据"
    assert payload["trace_id"] == trace["trace_id"]
    assert payload["method"] == "POST"
    assert payload["status_code"] == 201
