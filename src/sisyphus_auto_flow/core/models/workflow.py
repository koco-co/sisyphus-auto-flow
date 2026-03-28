"""Adaptive HAR workflow models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class WorkflowScenarioGroup(BaseModel):
    """A decomposed scenario group derived from a parsed HAR."""

    name: str = Field(description="场景组名称")
    module: str = Field(description="业务模块")
    request_sequences: list[int] = Field(default_factory=list, description="关联请求序号")
    endpoints: list[str] = Field(default_factory=list, description="关联接口路径")
    target_test_path: str = Field(description="推荐执行/生成的测试路径")


class WorkflowWriterTask(BaseModel):
    """A writer task unit for a worker agent."""

    agent: str = Field(default="test-writer", description="建议执行该任务的 Agent 角色")
    module: str = Field(description="业务模块")
    scenario_group: str = Field(description="场景组名称")
    target_test_path: str = Field(description="目标测试路径")
    request_sequences: list[int] = Field(default_factory=list, description="关联请求序号")


class WorkflowImpactedArea(BaseModel):
    """A user-facing impacted area summary item."""

    module: str = Field(description="业务模块")
    menu: str = Field(description="菜单/业务域")
    function: str = Field(description="功能点")
    code_locations: list[str] = Field(default_factory=list, description="涉及代码位置")


class HarWorkflowManifest(BaseModel):
    """The manifest used to coordinate adaptive HAR processing."""

    source_har: str = Field(description="源 HAR 文件名")
    release: str = Field(description="选定 release 分支")
    workflow_mode: Literal["single_agent", "multi_agent"] = Field(description="工作流模式")
    scenario_groups: list[WorkflowScenarioGroup] = Field(default_factory=list, description="拆解后的场景组")
    targeted_tests: list[str] = Field(default_factory=list, description="建议定向执行的测试路径")
    writer_tasks: list[WorkflowWriterTask] = Field(default_factory=list, description="待分发给 writer 的任务单元")
    impacted_areas: list[WorkflowImpactedArea] = Field(default_factory=list, description="影响范围摘要")
    har_scenarios: list[str] = Field(default_factory=list, description="HAR 原始场景摘要")
    supplemented_scenarios: list[str] = Field(default_factory=list, description="AI 补充场景摘要")
    skipped_items: list[str] = Field(default_factory=list, description="跳过或不纳入范围的项")
    follow_ups: list[str] = Field(default_factory=list, description="后续跟进项")
    parallel_writer_limit: int = Field(default=3, description="并行 writer 上限")
