"""数据驱动插件。

加载 YAML/JSON 格式的测试数据文件，用于 pytest 参数化。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from loguru import logger


def load_test_data(file_path: str | Path) -> list[dict[str, Any]]:
    """加载测试数据文件（支持 YAML 和 JSON）。

    Args:
        file_path: 数据文件路径

    Returns:
        测试数据列表
    """
    path = Path(file_path)
    assert path.exists(), f"测试数据文件不存在: {path}"

    if path.suffix in (".yaml", ".yml"):
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
    elif path.suffix == ".json":
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    else:
        msg = f"不支持的数据文件格式: {path.suffix}，仅支持 .yaml/.yml/.json"
        raise ValueError(msg)

    if isinstance(data, list):
        logger.info(f"加载测试数据: {path.name}，共 {len(data)} 条")
        return data
    if isinstance(data, dict):
        return [data]

    msg = f"测试数据格式错误，期望 list 或 dict，实际 {type(data)}"
    raise TypeError(msg)
