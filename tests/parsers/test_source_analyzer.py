"""Tests for workflow source reference discovery."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def test_collect_reference_sources_includes_backend_qa_and_env_paths(tmp_path: Path) -> None:
    """Source references should include backend repos, QA API definitions, and QA env config files."""
    from sisyphus_auto_flow.parsers.source_analyzer import collect_reference_sources

    repo_root = tmp_path / "repo"
    (repo_root / ".repos" / "dt-insight-web" / "dt-center-assets").mkdir(parents=True)
    (repo_root / ".repos" / "dt-insight-web" / "dt-center-metadata").mkdir(parents=True)
    (repo_root / ".repos" / "dt-insight-qa" / "dtstack-httprunner" / "api" / "assets").mkdir(parents=True)
    (repo_root / ".repos" / "dt-insight-qa" / "dtstack-httprunner" / "api" / "metadata").mkdir(parents=True)
    (repo_root / ".repos" / "dt-insight-qa" / "dtstack-httprunner" / "config").mkdir(parents=True)

    (repo_root / ".repos" / "dt-insight-qa" / "dtstack-httprunner" / "api" / "assets" / "assets_api.py").write_text(
        "# assets\n",
        encoding="utf-8",
    )
    (repo_root / ".repos" / "dt-insight-qa" / "dtstack-httprunner" / "api" / "metadata" / "metadata_api.py").write_text(
        "# metadata\n",
        encoding="utf-8",
    )
    (repo_root / ".repos" / "dt-insight-qa" / "dtstack-httprunner" / "config" / "configs.py").write_text(
        "# configs\n",
        encoding="utf-8",
    )
    (repo_root / ".repos" / "dt-insight-qa" / "dtstack-httprunner" / "config" / "env_config.py").write_text(
        "# env\n",
        encoding="utf-8",
    )

    references = collect_reference_sources(repo_root=repo_root, modules={"assets", "metadata"})

    assert references == [
        ".repos/dt-insight-web/dt-center-assets",
        ".repos/dt-insight-web/dt-center-metadata",
        ".repos/dt-insight-qa/dtstack-httprunner/api/assets/assets_api.py",
        ".repos/dt-insight-qa/dtstack-httprunner/api/metadata/metadata_api.py",
        ".repos/dt-insight-qa/dtstack-httprunner/config/configs.py",
        ".repos/dt-insight-qa/dtstack-httprunner/config/env_config.py",
    ]
