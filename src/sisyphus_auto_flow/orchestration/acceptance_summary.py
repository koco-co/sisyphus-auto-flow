"""Terminal-only acceptance summary rendering."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sisyphus_auto_flow.core.models.workflow import HarWorkflowManifest

if TYPE_CHECKING:
    from collections.abc import Mapping


def render_acceptance_summary(manifest: HarWorkflowManifest | Mapping[str, Any]) -> str:
    """Render the requested acceptance checklist as plain terminal text."""
    normalized = (
        manifest if isinstance(manifest, HarWorkflowManifest) else HarWorkflowManifest.model_validate(dict(manifest))
    )

    impacted_lines: list[str] = []
    for area in normalized.impacted_areas:
        impacted_lines.append(f"- {area.module} | {area.menu} | {area.function}")
        impacted_lines.extend(f"  - {location}" for location in area.code_locations)

    sections = [
        "验收清单",
        f"Release: {normalized.release}",
        "",
        "验收通知",
        normalized.acceptance_notice or "请按下列命令完成验收。",
        "",
        "参考源码",
        *[f"- {item}" for item in normalized.reference_sources],
        "",
        "HAR 给出场景",
        *[f"- {item}" for item in normalized.har_scenarios],
        "",
        "AI 补充场景",
        *[f"- {item}" for item in normalized.supplemented_scenarios],
        "",
        "涉及模块 / 菜单 / 功能",
        *(impacted_lines or ["- 无"]),
        "",
        "代码位置",
        *[f"- {location}" for area in normalized.impacted_areas for location in area.code_locations],
        "",
        "验收命令",
        *[f"- {item}" for item in normalized.validation_commands],
        "",
        "定向执行用例",
        *[f"- {item}" for item in normalized.targeted_tests],
        "",
        "跳过 / 不纳入范围",
        *[f"- {item}" for item in normalized.skipped_items],
        "",
        "后续跟进",
        *[f"- {item}" for item in normalized.follow_ups],
    ]
    return "\n".join(sections).strip() + "\n"
