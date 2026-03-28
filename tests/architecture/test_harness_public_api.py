"""Harness runtime public API characterization tests."""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def test_base_api_test_is_importable() -> None:
    """`BaseAPITest` should remain importable from the documented path."""
    from sisyphus_auto_flow.core.base import BaseAPITest

    assert BaseAPITest.__name__ == "BaseAPITest"


def test_pytest_can_load_harness_plugin(tmp_path: Path) -> None:
    """Pytest should be able to load the shipped harness plugin."""
    test_file = tmp_path / "test_plugin_load.py"
    test_file.write_text(
        """
def test_plugin_fixture_available(env_name):
    assert env_name == "dev"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "sisyphus_auto_flow.fixtures.conftest",
            str(test_file),
        ],
        capture_output=True,
        cwd=tmp_path,
        env=env,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_supported_runtime_exports_remain_importable() -> None:
    """Supported runtime entrypoints should stay importable for future package extraction."""
    import sisyphus_auto_flow as runtime_sdk
    from sisyphus_auto_flow.core import BaseAPITest
    from sisyphus_auto_flow.fixtures import AuthManager, CleanupManager, DatabaseHelper
    from sisyphus_auto_flow.generator import CodeGenerator, TemplateLocator
    from sisyphus_auto_flow.parsers import parse_har_file
    from sisyphus_auto_flow.plugins import ContractValidator, ReplayStore, build_trace_context

    assert runtime_sdk.__version__ == "0.1.0"
    assert runtime_sdk.BaseAPITest is BaseAPITest
    assert runtime_sdk.CodeGenerator is CodeGenerator
    assert runtime_sdk.TemplateLocator is TemplateLocator
    assert runtime_sdk.parse_har_file is parse_har_file
    assert AuthManager.__name__ == "AuthManager"
    assert CleanupManager.__name__ == "CleanupManager"
    assert DatabaseHelper.__name__ == "DatabaseHelper"
    assert ContractValidator.__name__ == "ContractValidator"
    assert ReplayStore.__name__ == "ReplayStore"
    assert callable(build_trace_context)


def test_legacy_harness_namespace_warns_but_keeps_base_api_test() -> None:
    """The deprecated harness namespace should still expose BaseAPITest through a warning shim."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        harness = importlib.import_module("sisyphus_auto_flow.harness")

    assert harness.BaseAPITest.__name__ == "BaseAPITest"
    assert any("已弃用" in str(item.message) for item in caught)
