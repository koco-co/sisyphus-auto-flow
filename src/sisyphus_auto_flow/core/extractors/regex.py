"""正则表达式变量提取。"""

from __future__ import annotations

import re


def extract_regex(text: str, pattern: str, group: int = 1) -> str:
    """从文本中使用正则表达式提取值。"""
    match = re.search(pattern, text)
    assert match is not None, f"正则匹配失败: {pattern}"
    return match.group(group)


def extract_regex_all(text: str, pattern: str) -> list[str]:
    """从文本中提取所有匹配值。"""
    return re.findall(pattern, text)
