"""Business workspace scaffold regression tests."""

from __future__ import annotations

from pathlib import Path


def test_metadata_module_scaffold_exists() -> None:
    """The real HAR metadata module should have parallel api/test/testdata scaffolds."""
    repo_root = Path(__file__).resolve().parents[2]

    assert (repo_root / "api" / "metadata" / "metadata_api.py").exists()
    assert (repo_root / "tests" / "metadata" / "conftest.py").exists()
    assert (repo_root / "testdata" / "metadata" / "__init__.py").exists()
