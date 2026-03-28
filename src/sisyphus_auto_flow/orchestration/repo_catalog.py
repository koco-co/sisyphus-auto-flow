"""Repository catalog helpers for release-aware source synchronization."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

DEFAULT_CATALOG_PATH = Path(__file__).resolve().parents[3] / "config" / "repositories.yaml"


class RepositoryEntry(BaseModel):
    """A single repository catalog entry."""

    name: str = Field(description="仓库名")
    clone_url: str = Field(description="clone 地址")
    include_in_sync: bool = Field(default=True, description="是否纳入标准同步流程")
    reason: str | None = Field(default=None, description="排除原因")


class RepositoryCatalog(BaseModel):
    """The fixed repository catalog stored in-repo."""

    default_release: str = Field(description="默认 release")
    supported_releases: list[str] = Field(default_factory=list, description="支持的 release 列表")
    repositories: list[RepositoryEntry] = Field(default_factory=list, description="仓库定义列表")

    def resolve_release(self, release: str | None = None) -> str:
        """Return a validated release, falling back to the catalog default."""
        selected = release or self.default_release
        if selected not in self.supported_releases:
            msg = f"Unsupported release: {selected}. Supported releases: {', '.join(self.supported_releases)}"
            raise ValueError(msg)
        return selected

    def sync_targets(self) -> list[RepositoryEntry]:
        """Return repositories that participate in the backend sync flow."""
        return [repo for repo in self.repositories if repo.include_in_sync]


def load_repository_catalog(path: Path = DEFAULT_CATALOG_PATH) -> RepositoryCatalog:
    """Load the fixed repository catalog from YAML."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return RepositoryCatalog.model_validate(data)
