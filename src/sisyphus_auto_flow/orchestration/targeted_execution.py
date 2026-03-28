"""Helpers for resolving targeted test execution scopes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sisyphus_auto_flow.core.models.workflow import HarWorkflowManifest

if TYPE_CHECKING:
    from collections.abc import Mapping


def resolve_targeted_tests(manifest: HarWorkflowManifest | Mapping[str, Any]) -> list[str]:
    """Return the deduplicated test targets from a workflow manifest."""
    normalized = (
        manifest if isinstance(manifest, HarWorkflowManifest) else HarWorkflowManifest.model_validate(dict(manifest))
    )
    ordered_targets = list(dict.fromkeys(normalized.targeted_tests))
    specific_file_targets = [target for target in ordered_targets if target.endswith(".py")]

    filtered: list[str] = []
    for target in ordered_targets:
        if target.endswith(".py"):
            filtered.append(target)
            continue
        if any(file_target.startswith(f"{target.rstrip('/')}/") for file_target in specific_file_targets):
            continue
        filtered.append(target)

    return filtered
