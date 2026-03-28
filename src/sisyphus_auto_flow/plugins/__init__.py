"""pytest 插件。

提供 Allure 增强、重试装饰器、数据驱动加载等功能。
"""

from sisyphus_auto_flow.plugins.allure_enhancer import (
    attach_request,
    attach_response,
)
from sisyphus_auto_flow.plugins.contract_testing import ContractValidator, schemathesis_available
from sisyphus_auto_flow.plugins.data_driver import load_test_data
from sisyphus_auto_flow.plugins.observability import attach_trace_metadata, build_trace_context
from sisyphus_auto_flow.plugins.replay import ReplayMode, ReplayStore, build_replay_key
from sisyphus_auto_flow.plugins.retry_handler import retry

__all__ = [
    "ContractValidator",
    "ReplayMode",
    "ReplayStore",
    "attach_request",
    "attach_response",
    "attach_trace_metadata",
    "build_replay_key",
    "build_trace_context",
    "load_test_data",
    "retry",
    "schemathesis_available",
]
