"""测试数据清理 pytest fixtures。

提供测试前后的数据清理机制，确保测试环境干净。
"""

from __future__ import annotations

from typing import Any

import pytest
from loguru import logger


class CleanupManager:
    """清理任务管理器。

    注册需要在测试结束后执行的清理 SQL，
    确保测试数据不会污染环境。
    """

    def __init__(self) -> None:
        self._tasks: list[tuple[str, list[Any] | None]] = []

    def register(self, sql: str, params: list[Any] | None = None) -> None:
        """注册清理 SQL。"""
        self._tasks.append((sql, params))
        logger.debug(f"注册清理任务: {sql}")

    def execute_all(self, db_helper: Any | None = None) -> None:
        """执行所有已注册的清理任务。"""
        if not self._tasks:
            return

        if db_helper is None:
            logger.warning("未提供数据库连接，跳过清理")
            return

        for sql, params in reversed(self._tasks):
            try:
                db_helper.execute(sql, params)
            except Exception:
                logger.warning(f"清理任务执行失败: {sql}")
        self._tasks.clear()
        logger.info("所有清理任务已完成")


@pytest.fixture
def cleanup() -> CleanupManager:
    """获取清理管理器实例。"""
    return CleanupManager()
