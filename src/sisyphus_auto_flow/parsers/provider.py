"""HAR provider 抽象。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from sisyphus_auto_flow.core.models.har import NormalizedHarResult


class HarProvider(ABC):
    """HAR 解析 provider 接口。"""

    name = "custom"

    def is_available(self) -> bool:
        """返回当前 provider 是否可用。"""
        return True

    @abstractmethod
    def parse(self, har_path: Path) -> NormalizedHarResult:
        """解析 HAR 文件并返回归一化结果。"""
