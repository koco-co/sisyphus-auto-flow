"""确定性回放支持。"""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from pathlib import Path
from typing import Any

import httpx


class ReplayMode(StrEnum):
    """回放模式。"""

    OFF = "off"
    RECORD = "record"
    REPLAY = "replay"


def build_replay_key(
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> str:
    """基于请求要素生成稳定 key。"""
    payload = {
        "method": method.upper(),
        "url": url,
        "params": params or {},
        "json": json_body or {},
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class ReplayStore:
    """基于 JSON 文件的最小回放存储。"""

    def __init__(self, root_dir: str | Path, *, mode: ReplayMode = ReplayMode.OFF) -> None:
        self._root_dir = Path(root_dir)
        self._mode = mode
        self._root_dir.mkdir(parents=True, exist_ok=True)

    def record(self, key: str, interaction: dict[str, Any]) -> Path:
        """录制一次交互。"""
        assert self._mode == ReplayMode.RECORD, "当前不是 record 模式"
        target = self._target_path(key)
        target.write_text(json.dumps(interaction, ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def replay(self, key: str) -> dict[str, Any]:
        """回放一次交互。"""
        assert self._mode == ReplayMode.REPLAY, "当前不是 replay 模式"
        target = self._target_path(key)
        assert target.exists(), f"未找到回放记录: {key}"
        return json.loads(target.read_text(encoding="utf-8"))

    def to_response(self, interaction: dict[str, Any], *, request: httpx.Request) -> httpx.Response:
        """将回放内容转换为 httpx.Response。"""
        return httpx.Response(
            status_code=int(interaction["status_code"]),
            headers=interaction.get("headers", {}),
            content=interaction.get("body", ""),
            request=request,
        )

    def _target_path(self, key: str) -> Path:
        return self._root_dir / f"{key}.json"
