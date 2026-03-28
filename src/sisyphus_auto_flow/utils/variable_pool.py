"""全局变量池。

提供跨测试步骤的变量存储和引用功能。
支持 ${var_name} 格式的变量替换。
"""

from __future__ import annotations

import re
import threading
from typing import Any

from loguru import logger


class VariablePool:
    """线程安全的全局变量池。

    用于在测试步骤之间传递数据（如：创建接口返回的 ID 传递给查询接口）。
    """

    _instance: VariablePool | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        if not hasattr(self, "_initialized"):
            self._data: dict[str, Any] = {}
            self._data_lock = threading.Lock()
            self._initialized = True

    def __new__(cls) -> VariablePool:
        """单例模式。"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def set(self, name: str, value: Any) -> None:
        """存入变量。"""
        with self._data_lock:
            self._data[name] = value
        logger.debug(f"变量池存入: {name} = {value}")

    def get(self, name: str) -> Any:
        """取出变量，不存在时抛出 KeyError。"""
        with self._data_lock:
            if name not in self._data:
                available = list(self._data.keys())
                msg = f"变量不存在: {name}，可用变量: {available}"
                raise KeyError(msg)
            return self._data[name]

    def get_or_default(self, name: str, default: Any = None) -> Any:
        """取出变量，不存在时返回默认值。"""
        with self._data_lock:
            return self._data.get(name, default)

    def resolve(self, text: str) -> str:
        """替换文本中的 ${var_name} 变量引用。"""

        def _replacer(match: re.Match[str]) -> str:
            var_name = match.group(1)
            with self._data_lock:
                if var_name in self._data:
                    return str(self._data[var_name])
            return match.group(0)

        return re.sub(r"\$\{(\w+)\}", _replacer, text)

    def clear(self) -> None:
        """清空变量池。"""
        with self._data_lock:
            self._data.clear()
        logger.debug("变量池已清空")

    def to_dict(self) -> dict[str, Any]:
        """导出为字典。"""
        with self._data_lock:
            return dict(self._data)

    def __contains__(self, name: object) -> bool:
        with self._data_lock:
            return name in self._data

    def __repr__(self) -> str:
        with self._data_lock:
            return f"VariablePool({list(self._data.keys())})"


# 全局变量池实例
global_pool = VariablePool()
