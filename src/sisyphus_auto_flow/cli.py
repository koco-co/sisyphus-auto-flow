"""命令行入口。"""

import click
from rich.console import Console

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
    # TODO: 实现 HAR 解析逻辑
    console.print("[yellow]HAR 解析功能尚未实现[/]")
