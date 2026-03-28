"""Documentation path/reference regression tests for the adaptive workflow."""

from __future__ import annotations

from pathlib import Path


def test_workflow_docs_reference_new_adaptive_entrypoints() -> None:
    """Core docs should mention the new release sync, planner, and acceptance entrypoints."""
    repo_root = Path(__file__).resolve().parents[2]
    docs = [
        repo_root / "README.md",
        repo_root / "CLAUDE.md",
        repo_root / ".claude" / "skills" / "har-to-testcase" / "SKILL.md",
    ]

    combined = "\n".join(path.read_text(encoding="utf-8") for path in docs)

    assert ".claude/scripts/sync_release_repos.sh" in combined
    assert ".claude/scripts/plan_har_workflow.sh" in combined
    assert ".claude/scripts/render_acceptance_summary.sh" in combined
    assert ".claude/agents/" in combined
    assert "Install.md" in combined
    assert "using-autoflow" in combined
