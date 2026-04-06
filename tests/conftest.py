"""插件单元测试的公共测试夹具。"""
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def sample_har_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample.har"


@pytest.fixture
def sample_dirty_har_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample_dirty.har"


@pytest.fixture
def sample_repo_profiles_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample_repo_profiles.yaml"


@pytest.fixture
def sample_response_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample_response.json"
