"""惯例扫描器 — AST 检测目标项目的 API URL 模式、HTTP 客户端、断言风格等规范。

输出 .autoflow/convention-scout.json 供 project-scanner 生成 convention-fingerprint.yaml。
"""
from __future__ import annotations

import argparse
import ast
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator

_EXCLUDED_DIRS = frozenset({".venv", "venv", "__pycache__", "node_modules", "dist", "build"})


def _iter_py_files(root: Path) -> Iterator[Path]:
    """遍历项目中的所有 .py 文件，排除无关目录。"""
    for py_file in root.rglob("*.py"):
        if any(part in _EXCLUDED_DIRS for part in py_file.parts):
            continue
        yield py_file


def _parse_ast(text: str, filename: str) -> ast.Module | None:
    """安全解析 Python 源码为 AST，语法错误返回 None。"""
    try:
        return ast.parse(text, filename=filename)
    except SyntaxError:
        return None


def _has_enum_base(node: ast.ClassDef) -> bool:
    """检查类是否继承自 Enum（支持 enum.Enum 和 Enum 两种写法）。"""
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id == "Enum":
            return True
        if isinstance(base, ast.Attribute) and base.attr == "Enum":
            return True
    return False


def _is_url_constant(node: ast.AST) -> bool:
    """检查 AST 节点是否是字符串常量赋值给全大写变量。"""
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if (isinstance(target, ast.Name)
                    and target.id.isupper()
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)):
                return True
    return False


def detect_api_pattern(project_root: Path) -> dict[str, Any]:
    """检测 API URL 定义模式：enum / dict / constant / inline。

    遍历 api/**/*.py，检查：
    - class XxxApi(Enum): xxx = 'path' → enum
    - APIS = {'xxx': 'path'}          → dict
    - XXX_URL = 'path'                → constant
    - 未检测到上述模式                 → inline
    """
    api_files = sorted(project_root.glob("api/**/*.py"))
    if not api_files:
        return {"type": "inline", "modules": []}

    parsed: list[tuple[Path, ast.Module]] = []
    for filepath in api_files:
        text = filepath.read_text()
        tree = _parse_ast(text, filename=str(filepath))
        if tree is not None:
            parsed.append((filepath, tree))

    # 检查 enum 模式
    enum_modules = []
    for filepath, tree in parsed:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and _has_enum_base(node):
                enum_modules.append({
                    "name": filepath.parent.name,
                    "class": node.name,
                    "location": str(filepath.relative_to(project_root)),
                })
                break

    if enum_modules:
        return {
            "type": "enum",
            "class_pattern": "{Module}Api",
            "value_access": ".value",
            "modules": enum_modules,
        }

    # 检查 dict / constant 模式
    for _, tree in parsed:
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        return {"type": "dict", "modules": []}

    for _, tree in parsed:
        for node in ast.walk(tree):
            if _is_url_constant(node):
                return {"type": "constant", "modules": []}

    return {"type": "inline", "modules": []}


def detect_http_client(project_root: Path) -> dict[str, Any]:
    """检测 HTTP 客户端：requests / httpx / aiohttp / direct + session 或直接调用。"""
    imports_requests = 0
    imports_httpx = 0
    imports_aiohttp = 0
    uses_session = False
    custom_classes: list[str] = []

    for py_file in _iter_py_files(project_root):
        try:
            text = py_file.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        tree = _parse_ast(text, filename=str(py_file))
        if tree is None:
            continue

        # AST 检测 import
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "requests":
                        imports_requests += 1
                    elif alias.name == "httpx":
                        imports_httpx += 1
                    elif alias.name == "aiohttp":
                        imports_aiohttp += 1
            elif isinstance(node, ast.ImportFrom):
                if node.module == "requests":
                    imports_requests += 1
                elif node.module == "httpx":
                    imports_httpx += 1
                elif node.module == "aiohttp":
                    imports_aiohttp += 1

        # AST 检测 requests.Session()
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "Session"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "requests"):
                uses_session = True
                break

        # AST 检测自定义包装类（包含 post/get/put/delete 的 request/client 类）
        for node in ast.walk(tree):
            if (isinstance(node, ast.ClassDef)
                    and ("request" in node.name.lower() or "client" in node.name.lower())):
                for item in ast.walk(node):
                    if (isinstance(item, ast.Call)
                            and isinstance(item.func, ast.Attribute)
                            and item.func.attr in ("post", "get", "put", "delete")):
                        custom_classes.append(node.name)
                        break

    if imports_httpx > imports_requests and imports_httpx > imports_aiohttp:
        lib = "httpx"
    elif imports_aiohttp > imports_requests and imports_aiohttp > imports_httpx:
        lib = "aiohttp"
    elif imports_requests > 0:
        lib = "requests"
    else:
        lib = "unknown"

    pattern: str = "custom_class" if custom_classes else ("session" if uses_session else "direct")

    return {
        "library": lib,
        "client_pattern": pattern,
        "custom_class": custom_classes[0] if custom_classes else None,
    }


def scan_project(project_root: Path) -> dict[str, Any]:
    """执行所有检测并返回完整的惯例指纹。"""
    return {
        "scanned_at": datetime.now(UTC).isoformat(),
        "api": detect_api_pattern(project_root),
        "http_client": detect_http_client(project_root),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AutoFlow convention scanner")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output", default=".autoflow/convention-scout.json")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    result = scan_project(root)

    out_path = root / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"Scout written to {out_path}")
