"""Tests for targeted execution scope resolution."""

from __future__ import annotations


def test_resolve_targeted_tests_prefers_specific_file_targets_over_parent_directories() -> None:
    """A file target should replace its broader parent directory when both are present."""
    from sisyphus_auto_flow.orchestration.targeted_execution import resolve_targeted_tests

    manifest = {
        "source_har": "assets.har",
        "release": "release_6.2.x",
        "workflow_mode": "multi_agent",
        "scenario_groups": [],
        "targeted_tests": [
            "tests/assets",
            "tests/assets/test_assets_crud.py",
            "tests/batch",
        ],
        "writer_tasks": [],
    }

    assert resolve_targeted_tests(manifest) == [
        "tests/assets/test_assets_crud.py",
        "tests/batch",
    ]
