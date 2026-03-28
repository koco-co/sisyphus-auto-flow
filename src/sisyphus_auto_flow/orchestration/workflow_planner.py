"""Adaptive HAR workflow planning helpers."""

from __future__ import annotations

import json
from collections import OrderedDict
from typing import TYPE_CHECKING

from sisyphus_auto_flow.core.models.workflow import (
    HarWorkflowManifest,
    WorkflowImpactedArea,
    WorkflowScenarioGroup,
    WorkflowWriterTask,
)

if TYPE_CHECKING:
    from pathlib import Path

    from sisyphus_auto_flow.core.models.har import NormalizedHarResult

DEFAULT_MULTI_AGENT_REQUEST_THRESHOLD = 8
DEFAULT_PARALLEL_WRITER_LIMIT = 3


def _group_requests_by_module(parsed: NormalizedHarResult) -> OrderedDict[str, list]:
    grouped: OrderedDict[str, list] = OrderedDict()
    for request in parsed.requests:
        module = request.module or "unmapped"
        grouped.setdefault(module, []).append(request)
    return grouped


def plan_har_workflow(
    parsed: NormalizedHarResult,
    *,
    release: str,
    multi_agent_request_threshold: int = DEFAULT_MULTI_AGENT_REQUEST_THRESHOLD,
) -> HarWorkflowManifest:
    """Plan an adaptive workflow from a normalized HAR result."""
    grouped = _group_requests_by_module(parsed)
    scenario_groups: list[WorkflowScenarioGroup] = []
    impacted_areas: list[WorkflowImpactedArea] = []

    for module, requests in grouped.items():
        module_description = requests[0].module_description or module
        target_test_path = f"tests/{module}"
        scenario_groups.append(
            WorkflowScenarioGroup(
                name=f"{module}-scenario",
                module=module,
                request_sequences=[request.sequence for request in requests],
                endpoints=[request.path for request in requests],
                target_test_path=target_test_path,
            )
        )
        impacted_areas.append(
            WorkflowImpactedArea(
                module=module,
                menu=module_description,
                function=" / ".join(dict.fromkeys(request.path for request in requests)),
                code_locations=[
                    f"api/{module}/",
                    target_test_path,
                    f"testdata/{module}/",
                ],
            )
        )

    workflow_mode = "single_agent"
    if len(grouped) > 1 or parsed.filtered_entries >= multi_agent_request_threshold:
        workflow_mode = "multi_agent"

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

    return HarWorkflowManifest(
        source_har=parsed.source,
        release=release,
        workflow_mode=workflow_mode,
        scenario_groups=scenario_groups,
        targeted_tests=sorted({group.target_test_path for group in scenario_groups}),
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
