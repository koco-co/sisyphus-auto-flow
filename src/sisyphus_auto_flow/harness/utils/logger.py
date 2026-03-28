"""日志工具。

基于 loguru 的统一日志配置，
提供请求/响应日志记录和 Allure 报告集成。
"""

from __future__ import annotations

import sys
from typing import Any

import allure
from loguru import logger

DEFAULT_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level:<8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)


def setup_logger(
    *,
    level: str = "INFO",
    log_file: str | None = None,
    rotation: str = "10 MB",
    fmt: str = DEFAULT_FORMAT,
) -> None:
    """配置全局日志。

    Args:
        level: 日志级别
        log_file: 日志文件路径
        rotation: 日志轮转策略
        fmt: 日志格式
    """
    logger.remove()
    logger.add(sys.stderr, format=fmt, level=level, colorize=True)

    if log_file:
        logger.add(log_file, format=fmt, level=level, rotation=rotation, encoding="utf-8", retention="7 days")


def log_request(method: str, url: str, body: Any = None) -> None:
    """记录 HTTP 请求。"""
    logger.info(f"➡️  请求: {method} {url}")
    if body:
        logger.debug(f"    请求体: {body}")


def log_response(status: int, body: Any = None, duration_ms: float = 0) -> None:
    """记录 HTTP 响应。"""
    emoji = "✅" if 200 <= status < 300 else "❌"
    logger.info(f"{emoji} 响应: {status} ({duration_ms:.0f}ms)")
    if body:
        logger.debug(f"    响应体: {str(body)[:500]}")


def attach_to_allure(name: str, content: str, attachment_type: Any = allure.attachment_type.TEXT) -> None:
    """将内容附加到 Allure 报告。"""
    allure.attach(content, name=name, attachment_type=attachment_type)
