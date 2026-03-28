"""全局 pytest fixtures。

提供项目级别的测试夹具，包括：
- HTTP 客户端管理
- 环境配置加载
- Allure 报告增强
"""

from __future__ import annotations

import os

import pytest
from loguru import logger


@pytest.fixture(scope="session", autouse=True)
def _configure_logging() -> None:
    """配置日志格式。"""
    logger.info("测试会话开始")


@pytest.fixture(scope="session")
def env_name() -> str:
    """获取当前测试环境名称。"""
    return os.getenv("TEST_ENV", "dev")


@pytest.fixture(scope="session", autouse=True)
def _disable_proxy() -> None:
    """禁用代理，防止影响测试请求。"""
    for key in ("http_proxy", "https_proxy", "all_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
        os.environ.pop(key, None)
