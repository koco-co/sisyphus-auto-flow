"""Tests for terminal-only acceptance summary rendering."""

from __future__ import annotations


def test_acceptance_summary_renders_requested_checklist_sections() -> None:
    """The rendered acceptance summary should include the required terminal checklist sections."""
    from sisyphus_auto_flow.orchestration.acceptance_summary import render_acceptance_summary

    manifest = {
        "source_har": "assets.har",
        "release": "release_6.2.x",
        "workflow_mode": "multi_agent",
        "har_scenarios": ["创建数据源", "查询数据源"],
        "supplemented_scenarios": ["删除数据源", "空名称校验"],
        "acceptance_notice": "请按下列命令完成验收，并核对参考源码与环境配置。",
        "reference_sources": [
            ".repos/dt-insight-web/dt-center-assets",
            ".repos/dt-insight-qa/dtstack-httprunner/config/env_config.py",
        ],
        "validation_commands": [
            "uv run pytest tests/assets/test_assets_crud.py -v --alluredir=allure-results",
            "bash .claude/scripts/render_acceptance_summary.sh .data/parsed/assets.workflow.json",
        ],
        "impacted_areas": [
            {
                "module": "assets",
                "menu": "数据资产",
                "function": "数据源管理",
                "code_locations": [
                    "api/assets/assets_api.py",
                    "tests/assets/test_assets_crud.py",
                ],
            }
        ],
        "targeted_tests": ["tests/assets/test_assets_crud.py"],
        "skipped_items": ["CustomItem 不在参考仓库范围内"],
        "follow_ups": ["等待真实 HAR 进行端到端回归"],
    }

    output = render_acceptance_summary(manifest)

    assert "验收通知" in output
    assert "参考源码" in output
    assert "HAR 给出场景" in output
    assert "AI 补充场景" in output
    assert "涉及模块 / 菜单 / 功能" in output
    assert "代码位置" in output
    assert "验收命令" in output
    assert "定向执行用例" in output
    assert "跳过 / 不纳入范围" in output
    assert "release_6.2.x" in output
