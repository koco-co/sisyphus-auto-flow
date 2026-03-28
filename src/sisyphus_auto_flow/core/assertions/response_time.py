"""响应时间断言。"""

from __future__ import annotations

import allure


def validate_response_time(duration_ms: float, max_ms: float) -> None:
    """断言响应时间不超过阈值。"""
    with allure.step(f"断言响应时间 <= {max_ms}ms"):
        assert duration_ms <= max_ms, f"响应时间超标: {duration_ms:.0f}ms > {max_ms}ms"


def validate_response_time_percentile(
    durations: list[float],
    percentile: float = 95.0,
    max_ms: float = 500.0,
) -> None:
    """断言响应时间百分位数。"""
    with allure.step(f"断言 P{percentile} 响应时间 <= {max_ms}ms"):
        if not durations:
            return
        sorted_d = sorted(durations)
        idx = min(int(len(sorted_d) * percentile / 100), len(sorted_d) - 1)
        p_value = sorted_d[idx]
        assert p_value <= max_ms, f"P{percentile} 响应时间超标: {p_value:.0f}ms > {max_ms}ms"
