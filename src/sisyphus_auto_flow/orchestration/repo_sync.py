"""Release-aware backend repository synchronization."""

from __future__ import annotations

import shutil
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from sisyphus_auto_flow.orchestration.repo_catalog import RepositoryCatalog


def _run_git(args: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        raise RuntimeError(f"git {' '.join(args)} failed: {message}")
    return result.stdout.strip()


def sync_repositories(
    catalog: RepositoryCatalog,
    workspace: Path,
    *,
    release: str | None = None,
    dry_run: bool = False,
) -> list[Path]:
    """Clone or update backend repositories to the selected release branch."""
    selected_release = catalog.resolve_release(release)
    workspace.mkdir(parents=True, exist_ok=True)
    backup_root = workspace.parent / ".trash" / "repo-snapshots"

    synced_paths: list[Path] = []
    for repo in catalog.sync_targets():
        repo_path = workspace / repo.resolve_local_path()
        release_ref = repo.resolve_release_ref(selected_release)
        synced_paths.append(repo_path)
        if dry_run:
            continue

        if not repo_path.exists():
            repo_path.parent.mkdir(parents=True, exist_ok=True)
            _run_git(
                [
                    "clone",
                    "--branch",
                    release_ref,
                    "--single-branch",
                    repo.clone_url,
                    str(repo_path),
                ]
            )
            continue

        if not (repo_path / ".git").exists():
            backup_path = backup_root / repo.resolve_local_path()
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            if backup_path.exists():
                shutil.rmtree(backup_path)
            shutil.move(str(repo_path), str(backup_path))
            repo_path.parent.mkdir(parents=True, exist_ok=True)
            _run_git(
                [
                    "clone",
                    "--branch",
                    release_ref,
                    "--single-branch",
                    repo.clone_url,
                    str(repo_path),
                ]
            )
            continue

        _run_git(["fetch", "origin", release_ref], cwd=repo_path)
        _run_git(["checkout", "-B", release_ref, f"origin/{release_ref}"], cwd=repo_path)
        _run_git(["pull", "--ff-only", "origin", release_ref], cwd=repo_path)

    return synced_paths
