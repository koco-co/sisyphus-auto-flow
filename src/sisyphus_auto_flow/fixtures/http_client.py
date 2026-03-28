"""HTTP 客户端 pytest fixtures。

提供预配置的 httpx 客户端实例。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx
import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(scope="session")
def http_client(env_config: dict[str, Any]) -> Generator[httpx.Client]:
    """创建会话级别的 HTTP 同步客户端。"""
    http_cfg = env_config.get("http", {})
    client = httpx.Client(
        base_url=http_cfg.get("base_url", "http://localhost:8080"),
        timeout=http_cfg.get("timeout", 30.0),
        verify=http_cfg.get("verify_ssl", True),
    )
    yield client
    client.close()


@pytest.fixture(scope="session")
def async_http_client(env_config: dict[str, Any]) -> Generator[httpx.AsyncClient]:
    """创建会话级别的 HTTP 异步客户端。"""
    http_cfg = env_config.get("http", {})
    client = httpx.AsyncClient(
        base_url=http_cfg.get("base_url", "http://localhost:8080"),
        timeout=http_cfg.get("timeout", 30.0),
        verify=http_cfg.get("verify_ssl", True),
    )
    yield client
