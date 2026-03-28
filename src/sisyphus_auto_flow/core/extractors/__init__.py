"""变量提取器。

提供 JSONPath、正则表达式、HTTP 响应头三种提取方式。
"""

from sisyphus_auto_flow.core.extractors.header import (
    extract_header,
    extract_set_cookie,
)
from sisyphus_auto_flow.core.extractors.jsonpath import (
    extract_jsonpath,
    extract_jsonpath_list,
)
from sisyphus_auto_flow.core.extractors.regex import (
    extract_regex,
    extract_regex_all,
)

__all__ = [
    "extract_header",
    "extract_jsonpath",
    "extract_jsonpath_list",
    "extract_regex",
    "extract_regex_all",
    "extract_set_cookie",
]
