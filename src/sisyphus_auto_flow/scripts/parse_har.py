"""HAR 文件解析脚本。

从 Chrome 导出的 HAR 文件中提取 API 请求信息，
过滤静态资源，识别请求链关联关系，输出结构化 JSON。

用法：
    python -m sisyphus_auto_flow.scripts.parse_har <har_file> [--output <path>]
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import click
from loguru import logger
from rich.console import Console
from rich.table import Table

from sisyphus_auto_flow.harness.models.har import HarEntry, HarFile

console = Console()

# 需要过滤的静态资源扩展名
STATIC_EXTENSIONS = {
    ".css",
    ".js",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".map",
    ".webp",
    ".avif",
}

# 需要过滤的 URL 路径模式
SKIP_URL_PATTERNS = [
    r"/static/",
    r"/assets/",
    r"/favicon",
    r"/manifest\.json",
    r"\.hot-update\.",
    r"sockjs-node",
    r"__webpack",
    r"google-analytics",
    r"googletagmanager",
    r"hotjar",
    r"sentry",
    r"/fonts/",
    r"/images/",
]

# API 响应的有效 Content-Type
API_CONTENT_TYPES = {
    "application/json",
    "application/xml",
    "text/json",
    "text/xml",
    "text/plain",
}


def _is_api_request(entry: HarEntry) -> bool:
    """判断是否为有效的 API 请求（非静态资源）。"""
    url = entry.request.url
    parsed = urlparse(url)
    path = parsed.path.lower()

    # 过滤静态资源扩展名
    if any(path.endswith(ext) for ext in STATIC_EXTENSIONS):
        return False

    # 过滤特定 URL 模式
    if any(re.search(pattern, url, re.IGNORECASE) for pattern in SKIP_URL_PATTERNS):
        return False

    # 检查响应 Content-Type
    response_ct = ""
    for header in entry.response.headers:
        if header.name.lower() == "content-type":
            response_ct = header.value.lower()
            break

    # 如果有响应 Content-Type，检查是否为 API 类型
    if response_ct:
        if any(ct in response_ct for ct in API_CONTENT_TYPES):
            return True
        # HTML 页面通常不是 API（除非是 API 文档）
        if "text/html" in response_ct:
            return False

    # 如果是 POST/PUT/PATCH/DELETE，大概率是 API 请求
    if entry.request.method.upper() in ("POST", "PUT", "PATCH", "DELETE"):
        return True

    # 默认保留 GET 请求（可能是 API 也可能不是）
    return True


def _extract_ids(data: Any, ids: set[str] | None = None) -> set[str]:
    """从数据中提取可能的 ID 值。"""
    if ids is None:
        ids = set()

    if isinstance(data, dict):
        for key, value in data.items():
            key_lower = key.lower()
            if (
                any(kw in key_lower for kw in ("id", "uuid", "key", "token"))
                and isinstance(value, int | str)
                and str(value).strip()
            ):
                ids.add(str(value))
            _extract_ids(value, ids)
    elif isinstance(data, list):
        for item in data:
            _extract_ids(item, ids)

    return ids


def _parse_body(text: str) -> dict[str, Any] | str | None:
    """尝试将文本解析为 JSON，失败则返回原始文本。"""
    if not text or not text.strip():
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return text if len(text) < 2000 else text[:2000] + "...(已截断)"


def _filter_headers(headers: dict[str, str]) -> dict[str, str]:
    """过滤请求头，移除敏感和无关信息。"""
    skip_headers = {
        "cookie",
        "set-cookie",
        "authorization",
        "sec-ch-ua",
        "sec-ch-ua-mobile",
        "sec-ch-ua-platform",
        "sec-fetch-dest",
        "sec-fetch-mode",
        "sec-fetch-site",
        "upgrade-insecure-requests",
        "cache-control",
        "pragma",
        "accept-encoding",
        "accept-language",
        "connection",
        "host",
        "origin",
        "referer",
        "user-agent",
        "if-none-match",
        "if-modified-since",
    }
    return {k: v for k, v in headers.items() if k.lower() not in skip_headers}


def parse_har_file(har_path: Path, output_path: Path | None = None) -> dict[str, Any]:
    """解析 HAR 文件，提取有效的 API 请求信息。

    Args:
        har_path: HAR 文件路径
        output_path: 输出 JSON 文件路径

    Returns:
        解析后的结构化数据
    """
    logger.info(f"开始解析 HAR 文件: {har_path}")

    # 读取并解析 HAR 文件
    raw = json.loads(har_path.read_text(encoding="utf-8"))
    har = HarFile.model_validate(raw)
    total = len(har.log.entries)
    logger.info(f"共 {total} 条请求记录")

    # 过滤 API 请求
    api_entries = [e for e in har.log.entries if _is_api_request(e)]
    logger.info(f"过滤后剩余 {len(api_entries)} 条 API 请求")

    # 收集所有响应中出现的 ID
    all_response_ids: dict[int, set[str]] = {}
    for i, entry in enumerate(api_entries):
        resp_body = _parse_body(entry.response.content.text)
        if isinstance(resp_body, dict):
            all_response_ids[i] = _extract_ids(resp_body)

    # 构建请求列表
    requests: list[dict[str, Any]] = []
    for seq, entry in enumerate(api_entries, start=1):
        parsed_url = urlparse(entry.request.url)
        path = parsed_url.path

        # 解析请求体和响应体
        req_body = None
        if entry.request.post_data:
            req_body = _parse_body(entry.request.post_data.text)

        resp_body = _parse_body(entry.response.content.text)

        # 提取响应中的 ID
        extracted_ids: list[str] = []
        if isinstance(resp_body, dict):
            extracted_ids = sorted(_extract_ids(resp_body))

        # 检测依赖关系
        depends_on: int | None = None
        req_text = json.dumps(req_body) if req_body else ""
        req_text += path
        for prev_seq, prev_ids in all_response_ids.items():
            if prev_seq >= seq - 1:
                break
            if any(pid in req_text for pid in prev_ids if len(pid) > 2):
                depends_on = prev_seq + 1
                break

        request_info: dict[str, Any] = {
            "sequence": seq,
            "method": entry.request.method,
            "path": path,
            "query_params": entry.request.query_dict or None,
            "headers": _filter_headers(entry.request.headers_dict),
            "body": req_body,
            "response_status": entry.response.status,
            "response_body": resp_body,
            "extracted_ids": extracted_ids or None,
            "depends_on": depends_on,
        }
        requests.append(request_info)

    # 构建输出
    result: dict[str, Any] = {
        "source": har_path.name,
        "parsed_at": datetime.now().isoformat(),
        "total_entries": total,
        "filtered_entries": len(api_entries),
        "requests": requests,
    }

    # 写入输出文件
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info(f"解析结果已写入: {output_path}")

    return result


def _move_to_trash(har_path: Path) -> None:
    """将已处理的 HAR 文件移入回收站。"""
    project_root = Path(__file__).resolve().parents[3]
    trash_dir = project_root / ".trash"
    trash_dir.mkdir(exist_ok=True)

    dest = trash_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{har_path.name}"
    shutil.move(str(har_path), str(dest))
    logger.info(f"HAR 文件已移入回收站: {dest}")


def _display_summary(result: dict[str, Any]) -> None:
    """使用 Rich 面板展示解析摘要。"""
    table = Table(title=f"📋 HAR 解析摘要 — {result['source']}", show_lines=True)
    table.add_column("序号", style="cyan", width=4)
    table.add_column("方法", style="bold", width=8)
    table.add_column("路径", style="green")
    table.add_column("状态码", style="yellow", width=6)
    table.add_column("依赖", style="dim", width=6)

    for req in result["requests"]:
        status_style = "green" if 200 <= req["response_status"] < 300 else "red"
        dep = str(req["depends_on"]) if req["depends_on"] else "-"
        table.add_row(
            str(req["sequence"]),
            req["method"],
            req["path"],
            f"[{status_style}]{req['response_status']}[/]",
            dep,
        )

    console.print()
    console.print(table)
    console.print(
        f"\n[bold]总计:[/] {result['total_entries']} 条记录 → [green]{result['filtered_entries']}[/] 条 API 请求"
    )


@click.command()
@click.argument("har_file", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), default=None, help="输出文件路径")
@click.option("--no-trash", is_flag=True, default=False, help="不移入回收站")
def main(har_file: Path, output: Path | None, no_trash: bool) -> None:
    """解析 HAR 文件，提取 API 请求信息。

    HAR_FILE: Chrome 导出的 HAR 文件路径
    """
    if output is None:
        output = Path("tmp") / f"parsed_{har_file.stem}.json"

    console.print(f"[bold green]🔍 正在解析 HAR 文件:[/] {har_file}")

    result = parse_har_file(har_file, output)

    _display_summary(result)

    console.print(f"\n[bold blue]📄 结果已输出到:[/] {output}")

    if not no_trash:
        _move_to_trash(har_file)
        console.print("[dim]HAR 文件已移入 .trash/ 回收站[/]")


if __name__ == "__main__":
    main()
