"""Helpers for choosing source-of-truth references during HAR planning."""

from __future__ import annotations

from pathlib import Path

_BACKEND_REFERENCE_PATHS = {
    "assets": [Path(".repos/dt-insight-web/dt-center-assets")],
    "metadata": [Path(".repos/dt-insight-web/dt-center-metadata")],
}

_QA_API_REFERENCE_PATHS = {
    "assets": [Path(".repos/dt-insight-qa/dtstack-httprunner/api/assets/assets_api.py")],
    "metadata": [Path(".repos/dt-insight-qa/dtstack-httprunner/api/metadata/metadata_api.py")],
}

_QA_ENVIRONMENT_PATHS = [
    Path(".repos/dt-insight-qa/dtstack-httprunner/config/configs.py"),
    Path(".repos/dt-insight-qa/dtstack-httprunner/config/env_config.py"),
]


def collect_reference_sources(*, repo_root: Path, modules: set[str]) -> list[str]:
    """Collect deterministic backend + QA reference paths for the planned modules."""
    references: list[Path] = []
    for module in sorted(modules):
        references.extend(_BACKEND_REFERENCE_PATHS.get(module, []))
    for module in sorted(modules):
        references.extend(_QA_API_REFERENCE_PATHS.get(module, []))
    references.extend(_QA_ENVIRONMENT_PATHS)

    discovered: list[str] = []
    seen: set[str] = set()
    for relative_path in references:
        absolute_path = repo_root / relative_path
        if not absolute_path.exists():
            continue
        normalized = relative_path.as_posix()
        if normalized in seen:
            continue
        seen.add(normalized)
        discovered.append(normalized)
    return discovered
