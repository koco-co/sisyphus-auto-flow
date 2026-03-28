"""Release-selection contract tests for the adaptive workflow."""

from __future__ import annotations

from pathlib import Path


def test_repository_catalog_defines_fixed_release_choices_and_default() -> None:
    """The project catalog should expose the fixed backend release choices and default."""
    from sisyphus_auto_flow.orchestration.repo_catalog import load_repository_catalog

    repo_root = Path(__file__).resolve().parents[2]
    catalog = load_repository_catalog(repo_root / "config" / "repositories.yaml")

    assert catalog.supported_releases == [
        "release_5.3.x",
        "release_6.0.x",
        "release_6.2.x",
        "release_6.3.x",
        "release_7.0.x",
    ]
    assert catalog.default_release == "release_6.2.x"
    assert "CustomItem" not in {repo.name for repo in catalog.repositories if repo.include_in_sync}
