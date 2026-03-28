"""兼容层 — 旧导入路径重定向到新位置。

所有从 ``sisyphus_auto_flow.harness`` 导入的符号已迁移到新路径：

- ``harness.base_test``     → ``core.base``
- ``harness.validators``    → ``core.assertions``
- ``harness.extractors``    → ``core.extractors``
- ``harness.models``        → ``core.models``
- ``harness.fixtures``      → ``fixtures``
- ``harness.plugins``       → ``plugins``
- ``harness.utils``         → ``utils``

此模块将在 v1.0 时移除。
"""

import warnings

warnings.warn(
    "sisyphus_auto_flow.harness 已弃用，请使用 sisyphus_auto_flow.core / fixtures / plugins / utils。"
    " 此兼容层将在 v1.0 移除。",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export core symbols for backward compatibility
from sisyphus_auto_flow.core.base import BaseAPITest  # noqa: E402, F401
