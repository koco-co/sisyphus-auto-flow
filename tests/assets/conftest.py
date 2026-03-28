"""数据资产模块 pytest fixtures。"""

from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="module", autouse=True)
def require_live_api(env_config: dict) -> None:
    """默认跳过依赖真实服务的用例，避免本地验证被外部环境阻塞。"""
    base_url = env_config.get("http", {}).get("base_url") or env_config.get("api", {}).get(
        "base_url", "http://localhost:8080"
    )
    if os.getenv("RUN_LIVE_API_TESTS") != "1":
        pytest.skip(f"live API tests are disabled for {base_url}; set RUN_LIVE_API_TESTS=1 to enable them")


@pytest.fixture(scope="module")
def assets_base_url(env_config: dict) -> str:
    """数据资产服务 base URL。"""
    return env_config.get("http", {}).get("base_url") or env_config.get("api", {}).get(
        "base_url", "http://localhost:8080"
    )
