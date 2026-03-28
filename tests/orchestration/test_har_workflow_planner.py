"""Tests for adaptive HAR workflow planning."""

from __future__ import annotations

from sisyphus_auto_flow.core.models.har import NormalizedHarRequest, NormalizedHarResult


def _request(sequence: int, *, path: str, module: str) -> NormalizedHarRequest:
    return NormalizedHarRequest(
        sequence=sequence,
        method="GET",
        path=path,
        module=module,
        module_api_dir=module,
        module_description=module,
        headers={},
        response_status=200,
    )


def test_small_har_stays_on_single_agent_flow() -> None:
    """A small, single-module HAR should keep the lightweight path."""
    from sisyphus_auto_flow.orchestration.workflow_planner import plan_har_workflow

    parsed = NormalizedHarResult(
        source="small.har",
        total_entries=2,
        filtered_entries=2,
        requests=[
            _request(1, path="/dassets/v1/dataDb/pageQuery", module="assets"),
            _request(2, path="/dassets/v1/dataDb/detail/1", module="assets"),
        ],
    )

    manifest = plan_har_workflow(parsed, release="release_6.2.x")

    assert manifest.workflow_mode == "single_agent"
    assert manifest.release == "release_6.2.x"
    assert manifest.scenario_groups
    assert all(target.startswith("tests/assets") for target in manifest.targeted_tests)


def test_large_multi_module_har_switches_to_multi_agent_flow() -> None:
    """A larger multi-module HAR should be decomposed into a multi-agent plan."""
    from sisyphus_auto_flow.orchestration.workflow_planner import plan_har_workflow

    parsed = NormalizedHarResult(
        source="large.har",
        total_entries=12,
        filtered_entries=12,
        requests=[
            _request(1, path="/dassets/v1/dataDb/pageQuery", module="assets"),
            _request(2, path="/dassets/v1/dataDb/detail/1", module="assets"),
            _request(3, path="/dassets/v1/dataDb/detail/2", module="assets"),
            _request(4, path="/dassets/v1/dataDb/detail/3", module="assets"),
            _request(5, path="/dassets/v1/dataDb/detail/4", module="assets"),
            _request(6, path="/dassets/v1/dataDb/detail/5", module="assets"),
            _request(7, path="/batch/v1/task/pageQuery", module="batch"),
            _request(8, path="/batch/v1/task/detail/1", module="batch"),
            _request(9, path="/batch/v1/task/detail/2", module="batch"),
            _request(10, path="/batch/v1/task/detail/3", module="batch"),
            _request(11, path="/batch/v1/task/detail/4", module="batch"),
            _request(12, path="/batch/v1/task/detail/5", module="batch"),
        ],
    )

    manifest = plan_har_workflow(parsed, release="release_6.2.x")

    assert manifest.workflow_mode == "multi_agent"
    assert len(manifest.scenario_groups) >= 2
    assert any(target.startswith("tests/assets") for target in manifest.targeted_tests)
    assert any(target.startswith("tests/batch") for target in manifest.targeted_tests)
    assert len(manifest.writer_tasks) >= 2


def test_multi_agent_flow_splits_same_module_requests_by_resource_area() -> None:
    """Large same-module HAR inputs should decompose by functional resource area."""
    from sisyphus_auto_flow.orchestration.workflow_planner import plan_har_workflow

    parsed = NormalizedHarResult(
        source="metadata.har",
        total_entries=8,
        filtered_entries=8,
        requests=[
            _request(1, path="/dmetadata/v1/syncTask/pageTask", module="metadata"),
            _request(2, path="/dmetadata/v1/syncTask/realTimeTableList", module="metadata"),
            _request(3, path="/dmetadata/v1/syncTask/add", module="metadata"),
            _request(4, path="/dmetadata/v1/dataSource/listMetadataDataSource", module="metadata"),
            _request(5, path="/dmetadata/v1/dataDb/realTimeDbList", module="metadata"),
            _request(6, path="/dmetadata/v1/dataTable/getTableLifeCycle", module="metadata"),
            _request(7, path="/dmetadata/v1/dataTable/queryTablePermission", module="metadata"),
            _request(8, path="/dmetadata/v1/metadataApply/getApplyStatus", module="metadata"),
        ],
    )

    manifest = plan_har_workflow(parsed, release="release_6.2.x")

    assert manifest.workflow_mode == "multi_agent"
    assert {group.name for group in manifest.scenario_groups} >= {
        "metadata-syncTask-scenario",
        "metadata-dataSource-scenario",
        "metadata-dataDb-scenario",
        "metadata-dataTable-scenario",
        "metadata-metadataApply-scenario",
    }
    assert set(manifest.targeted_tests) == {"tests/metadata"}
    assert len(manifest.writer_tasks) >= 5


def test_resource_area_falls_back_to_previous_segment_for_version_only_paths() -> None:
    """Version-only path tails should not become scenario resource names."""
    from sisyphus_auto_flow.orchestration.workflow_planner import _derive_resource_area

    assert _derive_resource_area("/datasource/v1/") == "datasource"


def test_planner_includes_reference_sources_and_validation_commands(monkeypatch) -> None:
    """The workflow manifest should carry source references and explicit validation commands."""
    from sisyphus_auto_flow.orchestration import workflow_planner

    parsed = NormalizedHarResult(
        source="assets.har",
        total_entries=2,
        filtered_entries=2,
        requests=[
            _request(1, path="/dassets/v1/dataDb/pageQuery", module="assets"),
            _request(2, path="/dmetadata/v1/dataTable/getTableLifeCycle", module="metadata"),
        ],
    )

    monkeypatch.setattr(
        workflow_planner,
        "collect_reference_sources",
        lambda *, repo_root, modules: [
            ".repos/dt-insight-web/dt-center-assets",
            ".repos/dt-insight-qa/dtstack-httprunner/config/env_config.py",
        ],
    )

    manifest = workflow_planner.plan_har_workflow(parsed, release="release_6.2.x")

    assert manifest.reference_sources == [
        ".repos/dt-insight-web/dt-center-assets",
        ".repos/dt-insight-qa/dtstack-httprunner/config/env_config.py",
    ]
    assert manifest.validation_commands == [
        "uv run pytest tests/assets tests/metadata -v --alluredir=allure-results",
        "bash .claude/scripts/render_acceptance_summary.sh .data/parsed/assets.workflow.json",
    ]
    assert "请按下列命令完成验收" in manifest.acceptance_notice
