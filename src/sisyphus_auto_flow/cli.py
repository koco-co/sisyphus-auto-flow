"""命令行入口。"""

from __future__ import annotations

import json
from pathlib import Path

import click
from rich.console import Console

from sisyphus_auto_flow.core.models.har import NormalizedHarResult
from sisyphus_auto_flow.orchestration.acceptance_summary import render_acceptance_summary
from sisyphus_auto_flow.orchestration.repo_catalog import load_repository_catalog
from sisyphus_auto_flow.orchestration.repo_sync import sync_repositories
from sisyphus_auto_flow.orchestration.workflow_planner import plan_har_workflow, write_workflow_manifest
from sisyphus_auto_flow.parsers.har_parser import parse_har_file

console = Console()


@click.group()
@click.version_option()
def main() -> None:
    """sisyphus-auto-flow: AI 驱动的接口自动化测试用例生成工作流。"""


@main.command()
@click.argument("har_file", type=click.Path(exists=True))
@click.option("--output", "-o", default="tmp/parsed_requests.json", help="输出文件路径")
def parse(har_file: str, output: str) -> None:
    """解析 HAR 文件，提取 API 请求信息。"""
    console.print(f"[bold green]正在解析 HAR 文件：[/] {har_file}")
    console.print(f"[bold blue]输出路径：[/] {output}")
    parse_har_file(Path(har_file), Path(output))
    console.print("[bold green]HAR 解析完成[/]")


@main.command("sync-repos")
@click.option("--release", default=None, help="要同步到的 release 分支")
@click.option("--workspace", default=".repos", help="目标源码目录")
@click.option("--dry-run", is_flag=True, help="仅展示计划，不执行 git 操作")
def sync_repos(release: str | None, workspace: str, dry_run: bool) -> None:
    """按固定仓库清单同步后端源码仓库。"""
    catalog = load_repository_catalog()
    selected_release = catalog.resolve_release(release)
    synced = sync_repositories(
        catalog,
        Path(workspace),
        release=selected_release,
        dry_run=dry_run,
    )
    console.print(f"[bold green]目标 release：[/] {selected_release}")
    for path in synced:
        console.print(f"- {path}")
    console.print("[bold green]仓库同步完成[/]" if not dry_run else "[bold yellow]Dry-run 完成[/]")


@main.command("plan-har")
@click.option("--har", "har_file", required=True, type=click.Path(exists=True), help="HAR 文件路径")
@click.option("--release", default=None, help="要参考的 release 分支")
@click.option("--output", required=True, type=click.Path(), help="输出 workflow manifest 的 JSON 文件")
@click.option("--multi-agent-threshold", default=8, type=int, help="切换到 multi-agent 的请求数阈值")
def plan_har(har_file: str, release: str | None, output: str, multi_agent_threshold: int) -> None:
    """解析 HAR 并生成自适应工作流 manifest。"""
    catalog = load_repository_catalog()
    selected_release = catalog.resolve_release(release)
    parsed = NormalizedHarResult.model_validate(parse_har_file(Path(har_file)))
    manifest = plan_har_workflow(
        parsed,
        release=selected_release,
        multi_agent_request_threshold=multi_agent_threshold,
    )
    write_workflow_manifest(manifest, Path(output))
    console.print(f"[bold green]workflow manifest 已生成：[/] {output}")


@main.command("render-acceptance")
@click.option("--manifest", required=True, type=click.Path(exists=True), help="workflow manifest JSON 路径")
def render_acceptance(manifest: str) -> None:
    """渲染终端验收清单。"""
    manifest_data = json.loads(Path(manifest).read_text(encoding="utf-8"))
    console.print(render_acceptance_summary(manifest_data))
