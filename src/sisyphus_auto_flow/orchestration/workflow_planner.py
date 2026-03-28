"""Adaptive HAR workflow planning helpers."""

from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path
from typing import TYPE_CHECKING

from sisyphus_auto_flow.core.models.workflow import (
    HarWorkflowManifest,
    WorkflowImpactedArea,
    WorkflowScenarioGroup,
    WorkflowWriterTask,
)
from sisyphus_auto_flow.parsers.source_analyzer import collect_reference_sources

if TYPE_CHECKING:
    from sisyphus_auto_flow.core.models.har import NormalizedHarResult

DEFAULT_MULTI_AGENT_REQUEST_THRESHOLD = 8
DEFAULT_PARALLEL_WRITER_LIMIT = 3
REPO_ROOT = Path(__file__).resolve().parents[3]


def _group_requests_by_module(parsed: NormalizedHarResult) -> OrderedDict[str, list]:
    grouped: OrderedDict[str, list] = OrderedDict()
    for request in parsed.requests:
        module = request.module or "unmapped"
        grouped.setdefault(module, []).append(request)
    return grouped


def _derive_resource_area(path: str) -> str:
    """Derive a stable functional area from a versioned API path."""
    segments = [segment for segment in path.split("/") if segment]
    for index, segment in enumerate(segments):
        if segment.startswith("v") and segment[1:].isdigit() and index + 1 < len(segments):
            return segments[index + 1]
    if not segments:
        return "unknown"

    candidate = segments[-1]
    if candidate.startswith("v") and candidate[1:].isdigit():
        return segments[-2] if len(segments) > 1 else "unknown"
    return candidate


def _group_requests_for_workflow(
    parsed: NormalizedHarResult,
    *,
    workflow_mode: str,
) -> OrderedDict[tuple[str, str], list]:
    grouped: OrderedDict[tuple[str, str], list] = OrderedDict()
    for request in parsed.requests:
        module = request.module or "unmapped"
        resource_area = module if workflow_mode == "single_agent" else _derive_resource_area(request.path)
        grouped.setdefault((module, resource_area), []).append(request)
    return grouped


def _build_validation_commands(*, source_har: str, targeted_tests: list[str]) -> list[str]:
    """Build explicit, copy-paste friendly validation commands for terminal acceptance."""
    workflow_stem = Path(source_har).stem
    targeted_command = " ".join(targeted_tests) if targeted_tests else "tests/"
    return [
        f"uv run pytest {targeted_command} -v --alluredir=allure-results",
        f"bash .claude/scripts/render_acceptance_summary.sh .data/parsed/{workflow_stem}.workflow.json",
    ]


def plan_har_workflow(
    parsed: NormalizedHarResult,
    *,
    release: str,
    multi_agent_request_threshold: int = DEFAULT_MULTI_AGENT_REQUEST_THRESHOLD,
) -> HarWorkflowManifest:
    """Plan an adaptive workflow from a normalized HAR result."""
    grouped_by_module = _group_requests_by_module(parsed)
    workflow_mode = "single_agent"
    if len(grouped_by_module) > 1 or parsed.filtered_entries >= multi_agent_request_threshold:
        workflow_mode = "multi_agent"

    grouped = _group_requests_for_workflow(parsed, workflow_mode=workflow_mode)
    scenario_groups: list[WorkflowScenarioGroup] = []
    impacted_areas: list[WorkflowImpactedArea] = []

    for (module, resource_area), requests in grouped.items():
        module_description = requests[0].module_description or module
        target_test_path = f"tests/{module}"
        scenario_name = (
            f"{module}-scenario" if workflow_mode == "single_agent" else f"{module}-{resource_area}-scenario"
        )
        scenario_groups.append(
            WorkflowScenarioGroup(
                name=scenario_name,
                module=module,
                request_sequences=[request.sequence for request in requests],
                endpoints=[request.path for request in requests],
                target_test_path=target_test_path,
            )
        )
        impacted_areas.append(
            WorkflowImpactedArea(
                module=module,
                menu=module_description
                if workflow_mode == "single_agent"
                else f"{module_description} / {resource_area}",
                function=" / ".join(dict.fromkeys(request.path for request in requests)),
                code_locations=[
                    f"api/{module}/",
                    target_test_path,
                    f"testdata/{module}/",
                ],
            )
        )

    writer_tasks = [
        WorkflowWriterTask(
            module=group.module,
            scenario_group=group.name,
            target_test_path=group.target_test_path,
            request_sequences=group.request_sequences,
        )
        for group in scenario_groups
    ]
    if workflow_mode == "single_agent":
        writer_tasks = []

    targeted_tests = sorted({group.target_test_path for group in scenario_groups})
    planned_modules = {group.module for group in scenario_groups if group.module != "unmapped"}
    reference_sources = collect_reference_sources(repo_root=REPO_ROOT, modules=planned_modules)
    validation_commands = _build_validation_commands(source_har=parsed.source, targeted_tests=targeted_tests)
    acceptance_notice = f"请按下列命令完成验收，并优先参考 {release} 基线下的后端源码与 dtstack-httprunner 环境配置。"

    return HarWorkflowManifest(
        source_har=parsed.source,
        release=release,
        workflow_mode=workflow_mode,
        acceptance_notice=acceptance_notice,
        scenario_groups=scenario_groups,
        targeted_tests=targeted_tests,
        reference_sources=reference_sources,
        validation_commands=validation_commands,
        writer_tasks=writer_tasks,
        impacted_areas=impacted_areas,
        har_scenarios=[group.name for group in scenario_groups],
        supplemented_scenarios=[],
        skipped_items=["CustomItem 不在标准后端参考范围内"],
        follow_ups=[],
        parallel_writer_limit=DEFAULT_PARALLEL_WRITER_LIMIT,
    )


def write_workflow_manifest(manifest: HarWorkflowManifest, output_path: Path) -> Path:
    """Persist a workflow manifest as JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path
