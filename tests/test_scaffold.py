"""Tests for scaffold generator — TDD (write first, implement second)."""
from pathlib import Path

from scripts.scaffold import ScaffoldConfig, generate_project


class TestGenerateProject:
    def _make_config(
        self,
        tmp_path: Path,
        *,
        project_name: str = "my-api",
        base_url: str = "http://172.16.115.247",
        db_configured: bool = False,
    ) -> ScaffoldConfig:
        return ScaffoldConfig(
            project_root=tmp_path,
            project_name=project_name,
            base_url=base_url,
            db_configured=db_configured,
        )

    def test_creates_directory_structure(self, tmp_path: Path) -> None:
        config = self._make_config(tmp_path)
        generate_project(config)

        assert (tmp_path / "tests" / "interface").is_dir()
        assert (tmp_path / "tests" / "scenariotest").is_dir()
        assert (tmp_path / "tests" / "unittest").is_dir()
        assert (tmp_path / "core").is_dir()
        assert (tmp_path / "core" / "models").is_dir()

    def test_creates_pyproject_toml(self, tmp_path: Path) -> None:
        config = self._make_config(tmp_path, project_name="billing")
        generate_project(config)

        content = (tmp_path / "pyproject.toml").read_text()
        assert "billing-tests" in content
        assert "pymysql" not in content

    def test_includes_pymysql_when_db_configured(self, tmp_path: Path) -> None:
        config = self._make_config(tmp_path, db_configured=True)
        generate_project(config)

        content = (tmp_path / "pyproject.toml").read_text()
        assert "pymysql" in content

    def test_creates_conftest(self, tmp_path: Path) -> None:
        config = self._make_config(tmp_path)
        generate_project(config)

        assert (tmp_path / "tests" / "conftest.py").is_file()

    def test_creates_core_files(self, tmp_path: Path) -> None:
        config = self._make_config(tmp_path)
        generate_project(config)

        assert (tmp_path / "core" / "__init__.py").is_file()
        assert (tmp_path / "core" / "client.py").is_file()
        assert (tmp_path / "core" / "assertions.py").is_file()
        assert (tmp_path / "core" / "models" / "__init__.py").is_file()

    def test_does_not_overwrite_existing(self, tmp_path: Path) -> None:
        config = self._make_config(tmp_path)
        # pre-create pyproject.toml with sentinel content
        (tmp_path / "pyproject.toml").write_text("existing content")
        generate_project(config)

        content = (tmp_path / "pyproject.toml").read_text()
        assert content == "existing content"

    def test_creates_gitignore(self, tmp_path: Path) -> None:
        config = self._make_config(tmp_path)
        generate_project(config)

        content = (tmp_path / ".gitignore").read_text()
        assert ".autoflow/" in content
        assert ".repos/" in content
        assert ".env" in content

    def test_creates_makefile(self, tmp_path: Path) -> None:
        config = self._make_config(tmp_path)
        generate_project(config)

        content = (tmp_path / "Makefile").read_text()
        assert "test-all" in content
        assert "test-interface" in content
