"""Regression tests for live API gating."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_assets_suite_is_skipped_when_live_api_mode_is_disabled() -> None:
    """Default test runs should skip live API suites unless explicitly enabled."""
    repo_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env.pop("RUN_LIVE_API_TESTS", None)

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/assets/test_assets_crud.py", "-q"],
        capture_output=True,
        cwd=repo_root,
        env=env,
        text=True,
        check=False,
    )

    combined_output = result.stdout + result.stderr
    assert result.returncode == 0, combined_output
    assert "skipped" in combined_output.lower()
