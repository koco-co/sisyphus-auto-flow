"""业务模块映射注册表。

定义 URL 前缀 → 业务模块 → 目录结构的完整映射。
所有映射均可枚举，供 HAR 解析器和代码生成器使用。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class BusinessModule(StrEnum):
    """业务模块枚举。"""

    ASSETS = "assets"
    METADATA = "metadata"
    BATCH = "batch"
    STREAM = "stream"
    DATASOURCE = "datasource"
    TAG = "tag"
    EASYINDEX = "easyindex"
    DATAAPI = "dataapi"
    CONSOLE = "console"
    UIC = "uic"


@dataclass(frozen=True)
class ModuleMapping:
    """单个模块的完整映射信息。"""

    module: BusinessModule
    url_prefixes: tuple[str, ...]
    api_dir: str
    test_dir: str
    data_dir: str
    sub_modules: tuple[str, ...] = ()
    description: str = ""


# 全量映射注册表
MODULE_REGISTRY: tuple[ModuleMapping, ...] = (
    ModuleMapping(
        module=BusinessModule.ASSETS,
        url_prefixes=("/dassets/v1/", "/api/v1/assets/"),
        api_dir="assets",
        test_dir="assets",
        data_dir="assets",
        sub_modules=("data_map", "metadata", "datasource", "data_security", "lineage"),
        description="数据资产管理平台",
    ),
    ModuleMapping(
        module=BusinessModule.METADATA,
        url_prefixes=("/dmetadata/v1/",),
        api_dir="metadata",
        test_dir="metadata",
        data_dir="metadata",
        sub_modules=(
            "sync_task",
            "data_source",
            "data_db",
            "data_table",
            "data_subscribe",
            "metadata_apply",
        ),
        description="元数据中心",
    ),
    ModuleMapping(
        module=BusinessModule.BATCH,
        url_prefixes=("/batch/v1/", "/api/v1/batch/"),
        api_dir="batch",
        test_dir="batch",
        data_dir="batch",
        sub_modules=("task", "schedule", "resource"),
        description="离线开发（批处理）",
    ),
    ModuleMapping(
        module=BusinessModule.STREAM,
        url_prefixes=("/stream/v1/", "/api/v1/stream/"),
        api_dir="stream",
        test_dir="stream",
        data_dir="stream",
        sub_modules=("task", "source", "sink"),
        description="实时开发（流处理）",
    ),
    ModuleMapping(
        module=BusinessModule.DATASOURCE,
        url_prefixes=("/datasource/v1/", "/api/v1/datasource/"),
        api_dir="datasource",
        test_dir="datasource",
        data_dir="datasource",
        sub_modules=("connection", "type"),
        description="数据源管理",
    ),
    ModuleMapping(
        module=BusinessModule.TAG,
        url_prefixes=("/tag/v1/", "/api/v1/tag/"),
        api_dir="tag",
        test_dir="tag",
        data_dir="tag",
        sub_modules=("tag_group", "tag_rule"),
        description="标签引擎",
    ),
    ModuleMapping(
        module=BusinessModule.EASYINDEX,
        url_prefixes=("/easyindex/v1/", "/api/v1/easyindex/"),
        api_dir="easyindex",
        test_dir="easyindex",
        data_dir="easyindex",
        sub_modules=("indicator", "dimension"),
        description="指标管理",
    ),
    ModuleMapping(
        module=BusinessModule.DATAAPI,
        url_prefixes=("/dataapi/v1/", "/api/v1/dataapi/"),
        api_dir="dataapi",
        test_dir="dataapi",
        data_dir="dataapi",
        sub_modules=("api_group", "api_definition"),
        description="数据 API",
    ),
    ModuleMapping(
        module=BusinessModule.CONSOLE,
        url_prefixes=("/console/v1/", "/api/v1/console/"),
        api_dir="console",
        test_dir="console",
        data_dir="console",
        sub_modules=("cluster", "tenant", "project"),
        description="控制台",
    ),
    ModuleMapping(
        module=BusinessModule.UIC,
        url_prefixes=("/uic/v1/", "/api/v1/uic/"),
        api_dir="uic",
        test_dir="uic",
        data_dir="uic",
        sub_modules=("user", "role", "permission"),
        description="用户中心",
    ),
)

# URL 前缀 → 模块的快速查找索引
_PREFIX_INDEX: dict[str, ModuleMapping] = {
    prefix: mapping for mapping in MODULE_REGISTRY for prefix in mapping.url_prefixes
}


def resolve_module(url: str) -> ModuleMapping | None:
    """根据 URL 解析所属业务模块。

    Args:
        url: 请求 URL 路径（如 /dassets/v1/dataSearch/dblist）

    Returns:
        匹配的模块映射，未匹配返回 None。

    """
    for prefix, mapping in _PREFIX_INDEX.items():
        if url.startswith(prefix):
            return mapping
    return None


def list_modules() -> list[BusinessModule]:
    """返回所有已注册的业务模块。"""
    return [m.module for m in MODULE_REGISTRY]
