"""内置 HAR provider。"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sisyphus_auto_flow.core.models.har import HarFile, NormalizedHarResult
from sisyphus_auto_flow.parsers.har_parser import _normalize_entries
from sisyphus_auto_flow.parsers.provider import HarProvider

if TYPE_CHECKING:
    from pathlib import Path


class CustomHarProvider(HarProvider):
    """基于项目内置 Pydantic 模型的 HAR provider。"""

    name = "custom"

    def parse(self, har_path: Path) -> NormalizedHarResult:
        raw = json.loads(har_path.read_text(encoding="utf-8"))
        har = HarFile.model_validate(raw)
        return _normalize_entries(har_path.name, len(har.log.entries), har.log.entries)
