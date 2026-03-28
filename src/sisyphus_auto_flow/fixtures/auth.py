"""认证相关 pytest fixtures。

提供 token 获取、注入、管理功能。
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest
from loguru import logger


class AuthManager:
    """认证管理器。"""

    def __init__(self, base_url: str, login_path: str = "/api/v1/auth/login") -> None:
        self._base_url = base_url
        self._login_path = login_path
        self._token: str | None = None
        self._client = httpx.Client(base_url=base_url, timeout=30.0)

    def login(self, username: str, password: str) -> str:
        """执行登录获取 token。"""
        response = self._client.post(
            self._login_path,
            json={"username": username, "password": password},
        )
        response.raise_for_status()
        data = response.json()
        self._token = (
            data.get("token")
            or data.get("data", {}).get("token")
            or data.get("access_token")
            or data.get("data", {}).get("access_token")
        )
        if self._token:
            logger.info(f"登录成功，获取到 token: {self._token[:20]}...")
        return self._token or ""

    def get_headers(self) -> dict[str, str]:
        """获取带认证信息的请求头。"""
        if not self._token:
            return {}
        return {"Authorization": f"Bearer {self._token}"}

    @property
    def token(self) -> str | None:
        return self._token

    def close(self) -> None:
        self._client.close()


@pytest.fixture(scope="session")
def auth_manager(env_config: dict[str, Any]) -> AuthManager:
    """创建认证管理器实例。"""
    base_url = env_config.get("http", {}).get("base_url", "http://localhost:8080")
    login_path = env_config.get("auth", {}).get("login_path", "/api/v1/auth/login")
    return AuthManager(base_url=base_url, login_path=login_path)


@pytest.fixture(scope="session")
def auth_token(auth_manager: AuthManager, env_config: dict[str, Any]) -> str:
    """获取认证 token。"""
    username = env_config.get("auth", {}).get("username", "admin")
    password = env_config.get("auth", {}).get("password", "admin123")
    return auth_manager.login(username, password)


@pytest.fixture
def auth_headers(auth_manager: AuthManager) -> dict[str, str]:
    """获取带认证信息的请求头。"""
    return auth_manager.get_headers()
