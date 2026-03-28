"""Contract tests for the adaptive agent workflow files."""

from __future__ import annotations

from pathlib import Path


def test_adaptive_workflow_agents_and_skill_exist() -> None:
    """The repo should define the new agent prompts and onboarding skill."""
    repo_root = Path(__file__).resolve().parents[2]
    expected_agent_files = [
        repo_root / ".claude" / "agents" / "har-decomposer.md",
        repo_root / ".claude" / "agents" / "scenario-planner.md",
        repo_root / ".claude" / "agents" / "test-writer.md",
        repo_root / ".claude" / "agents" / "test-reviewer.md",
        repo_root / ".claude" / "agents" / "targeted-executor.md",
    ]

    for agent_file in expected_agent_files:
        assert agent_file.exists(), f"missing agent contract: {agent_file}"
        content = agent_file.read_text(encoding="utf-8")
        assert "workflow manifest" in content.lower() or "workflow.json" in content

    using_skill = repo_root / ".claude" / "skills" / "using-autoflow" / "SKILL.md"
    assert using_skill.exists()

    skill_text = using_skill.read_text(encoding="utf-8")
    assert "Install.md" in skill_text
    assert "release_6.2.x" in skill_text
