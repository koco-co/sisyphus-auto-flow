"""项目级 pytest 配置。

加载环境配置并提供全局测试夹具。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
import yaml

pytest_plugins = [
    "sisyphus_auto_flow.harness.conftest",
]

# 项目根目录
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """深度合并两个字典，override 覆盖 base 中的同名键。"""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _resolve_env_vars(data: Any) -> Any:
    """递归解析配置中的 ${ENV_VAR} 环境变量引用。"""
    if isinstance(data, str) and data.startswith("${") and data.endswith("}"):
        env_key = data[2:-1]
        return os.getenv(env_key, "")
    if isinstance(data, dict):
        return {k: _resolve_env_vars(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_resolve_env_vars(item) for item in data]
    return data


@pytest.fixture(scope="session")
def env_config() -> dict[str, Any]:
    """加载环境配置。

    合并 config/base.yaml 和 config/{env}.yaml，
    环境名称从 TEST_ENV 环境变量读取，默认 dev。
    """
    env_name = os.getenv("TEST_ENV", "dev")
    config_dir = _PROJECT_ROOT / "config"

    # 加载基础配置
    base_file = config_dir / "base.yaml"
    base_config: dict[str, Any] = {}
    if base_file.exists():
        base_config = yaml.safe_load(base_file.read_text(encoding="utf-8")) or {}

    # 加载环境配置
    env_file = config_dir / f"{env_name}.yaml"
    env_override: dict[str, Any] = {}
    if env_file.exists():
        env_override = yaml.safe_load(env_file.read_text(encoding="utf-8")) or {}

    # 深度合并
    merged = _deep_merge(base_config, env_override)

    # 解析环境变量
    resolved = _resolve_env_vars(merged)

    return resolved
