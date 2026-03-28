"""hario-core HAR provider。"""

from __future__ import annotations

import importlib
import importlib.util
from typing import TYPE_CHECKING

from sisyphus_auto_flow.core.models.har import HarFile, NormalizedHarResult
from sisyphus_auto_flow.parsers.har_parser import _normalize_entries
from sisyphus_auto_flow.parsers.provider import HarProvider

if TYPE_CHECKING:
    from pathlib import Path


class HarioCoreHarProvider(HarProvider):
    """基于 hario-core 的可选 HAR provider。"""

    name = "hario-core"

    def is_available(self) -> bool:
        """返回 hario-core 是否已安装。"""
        return importlib.util.find_spec("hario_core") is not None

    def parse(self, har_path: Path) -> NormalizedHarResult:
        if not self.is_available():
            raise RuntimeError("hario-core is not installed")

        parse_module = importlib.import_module("hario_core.parse")
        parse_hario = parse_module.parse
        parsed = parse_hario(str(har_path))
        raw_log = parsed.model_dump() if hasattr(parsed, "model_dump") else {"entries": []}
        har = HarFile.model_validate({"log": raw_log})
        return _normalize_entries(har_path.name, len(har.log.entries), har.log.entries)
