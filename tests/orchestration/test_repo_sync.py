"""Tests for release-aware backend repository synchronization."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from pathlib import Path


def _git(*args: str, cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def _create_seed_remote(tmp_path: Path, name: str, release_ref: str) -> Path:
    remote = tmp_path / f"{name}.git"
    seed = tmp_path / f"{name}-seed"
    remote.mkdir(parents=True, exist_ok=True)
    seed.mkdir(parents=True, exist_ok=True)

    _git("init", "--bare", cwd=remote)
    _git("init", cwd=seed)
    _git("config", "user.name", "pytest", cwd=seed)
    _git("config", "user.email", "pytest@example.com", cwd=seed)

    (seed / "README.md").write_text(f"{name}\n", encoding="utf-8")
    _git("add", "README.md", cwd=seed)
    _git("commit", "-m", "initial", cwd=seed)
    _git("branch", "-M", "main", cwd=seed)
    _git("remote", "add", "origin", str(remote), cwd=seed)
    _git("push", "-u", "origin", "main", cwd=seed)

    _git("checkout", "-b", release_ref, cwd=seed)
    (seed / "version.txt").write_text("v1\n", encoding="utf-8")
    _git("add", "version.txt", cwd=seed)
    _git("commit", "-m", "release-v1", cwd=seed)
    _git("push", "-u", "origin", release_ref, cwd=seed)

    return remote


def _write_catalog(
    path: Path,
    *,
    name: str = "engine-plugins",
    clone_url: str,
    release: str,
    local_path: str = "dt-insight-engine/engine-plugins",
    release_ref_template: str = "{release}",
) -> Path:
    path.write_text(
        yaml.safe_dump(
            {
                "default_release": release,
                "supported_releases": [
                    "release_5.3.x",
                    "release_6.0.x",
                    "release_6.2.x",
                    "release_6.3.x",
                    "release_7.0.x",
                ],
                "repositories": [
                    {
                        "name": name,
                        "local_path": local_path,
                        "clone_url": clone_url,
                        "release_ref_template": release_ref_template,
                        "include_in_sync": True,
                    },
                    {
                        "name": "CustomItem",
                        "local_path": "CustomItem",
                        "clone_url": clone_url,
                        "include_in_sync": False,
                    },
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def test_sync_repositories_clones_missing_repo_and_skips_excluded_entries(tmp_path: Path) -> None:
    """Sync should clone missing repos for the selected release and skip excluded repos."""
    from sisyphus_auto_flow.orchestration.repo_catalog import load_repository_catalog
    from sisyphus_auto_flow.orchestration.repo_sync import sync_repositories

    release = "release_6.2.x"
    remote = _create_seed_remote(tmp_path, "engine-plugins", release)
    catalog_path = _write_catalog(tmp_path / "repositories.yaml", clone_url=str(remote), release=release)
    workspace = tmp_path / "repos"

    catalog = load_repository_catalog(catalog_path)
    sync_repositories(catalog, workspace, release=release)

    synced_repo = workspace / "dt-insight-engine" / "engine-plugins"
    assert synced_repo.exists()
    assert _git("rev-parse", "--abbrev-ref", "HEAD", cwd=synced_repo) == release
    assert (synced_repo / "version.txt").read_text(encoding="utf-8").strip() == "v1"
    assert not (workspace / "CustomItem").exists()


def test_sync_repositories_fast_forwards_existing_repo_to_latest_release_commit(tmp_path: Path) -> None:
    """Re-running sync should update an existing local checkout to the latest release commit."""
    from sisyphus_auto_flow.orchestration.repo_catalog import load_repository_catalog
    from sisyphus_auto_flow.orchestration.repo_sync import sync_repositories

    release = "release_6.2.x"
    remote = _create_seed_remote(tmp_path, "engine-plugins", release)
    catalog_path = _write_catalog(tmp_path / "repositories.yaml", clone_url=str(remote), release=release)
    catalog = load_repository_catalog(catalog_path)
    workspace = tmp_path / "repos"

    sync_repositories(catalog, workspace, release=release)
    synced_repo = workspace / "dt-insight-engine" / "engine-plugins"

    update_seed = tmp_path / "update-seed"
    _git("clone", str(remote), str(update_seed), cwd=tmp_path)
    _git("config", "user.name", "pytest", cwd=update_seed)
    _git("config", "user.email", "pytest@example.com", cwd=update_seed)
    _git("checkout", release, cwd=update_seed)
    (update_seed / "version.txt").write_text("v2\n", encoding="utf-8")
    _git("add", "version.txt", cwd=update_seed)
    _git("commit", "-m", "release-v2", cwd=update_seed)
    _git("push", "origin", release, cwd=update_seed)

    sync_repositories(catalog, workspace, release=release)

    assert (synced_repo / "version.txt").read_text(encoding="utf-8").strip() == "v2"


def test_sync_repositories_replaces_non_git_snapshot_directory_with_fresh_clone(tmp_path: Path) -> None:
    """A pre-existing source snapshot without .git metadata should be backed up and replaced."""
    from sisyphus_auto_flow.orchestration.repo_catalog import load_repository_catalog
    from sisyphus_auto_flow.orchestration.repo_sync import sync_repositories

    release = "release_6.2.x"
    remote = _create_seed_remote(tmp_path, "engine-plugins", release)
    catalog_path = _write_catalog(tmp_path / "repositories.yaml", clone_url=str(remote), release=release)
    catalog = load_repository_catalog(catalog_path)
    workspace = tmp_path / "repos"
    snapshot = workspace / "dt-insight-engine" / "engine-plugins"
    snapshot.mkdir(parents=True, exist_ok=True)
    (snapshot / "snapshot.txt").write_text("legacy snapshot\n", encoding="utf-8")

    sync_repositories(catalog, workspace, release=release)

    backup = tmp_path / ".trash" / "repo-snapshots" / "dt-insight-engine" / "engine-plugins"
    assert backup.exists()
    assert (backup / "snapshot.txt").read_text(encoding="utf-8").strip() == "legacy snapshot"
    assert (workspace / "dt-insight-engine" / "engine-plugins" / ".git").exists()


def test_sync_repositories_supports_release_ref_templates(tmp_path: Path) -> None:
    """Repositories should support release branch templates like dataAssets/release_6.2.x."""
    from sisyphus_auto_flow.orchestration.repo_catalog import load_repository_catalog
    from sisyphus_auto_flow.orchestration.repo_sync import sync_repositories

    release = "release_6.2.x"
    release_ref = f"dataAssets/{release}"
    remote = _create_seed_remote(tmp_path, "dt-insight-studio", release_ref)
    catalog_path = _write_catalog(
        tmp_path / "repositories.yaml",
        name="dt-insight-studio",
        clone_url=str(remote),
        release=release,
        local_path="dt-insight-front/dt-insight-studio",
        release_ref_template="dataAssets/{release}",
    )
    catalog = load_repository_catalog(catalog_path)
    workspace = tmp_path / "repos"

    sync_repositories(catalog, workspace, release=release)

    synced_repo = workspace / "dt-insight-front" / "dt-insight-studio"
    assert synced_repo.exists()
    assert _git("rev-parse", "--abbrev-ref", "HEAD", cwd=synced_repo) == release_ref
