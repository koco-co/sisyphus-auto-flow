"""测试基类模块。

所有接口自动化测试用例必须继承 BaseAPITest 类。
提供统一的 HTTP 客户端管理、变量池、标准断言方法和 Allure 报告增强。
"""

from __future__ import annotations

import re
import time
import uuid
from typing import Any, ClassVar

import allure
import httpx
from jsonpath_ng.ext import parse as jsonpath_parse
from loguru import logger


class BaseAPITest:
    """接口自动化测试基类。

    提供以下能力：
    - HTTP 请求发送（基于 httpx）
    - 变量池管理（跨步骤数据传递）
    - 标准断言方法（状态码、JSON、数据库、响应时间）
    - 变量提取（JSONPath、正则、Header）
    - Allure 报告增强
    """

    # 子类可覆盖的配置
    BASE_URL: ClassVar[str] = ""
    DEFAULT_HEADERS: ClassVar[dict[str, str]] = {}
    DEFAULT_TIMEOUT: ClassVar[float] = 30.0
    PRE_SQL: ClassVar[list[str]] = []

    def setup_method(self) -> None:
        """每个测试方法执行前的初始化。"""
        self._client = httpx.Client(
            base_url=self.BASE_URL,
            headers=self.DEFAULT_HEADERS,
            timeout=self.DEFAULT_TIMEOUT,
        )
        self._variables: dict[str, Any] = {}
        self._unique_id = uuid.uuid4().hex[:8]
        self._last_response_time: float = 0.0
        logger.info(f"测试初始化完成，唯一标识: {self._unique_id}")

    def teardown_method(self) -> None:
        """每个测试方法执行后的清理。"""
        if hasattr(self, "_client"):
            self._client.close()
        logger.info("测试清理完成")

    @property
    def unique_id(self) -> str:
        """获取当前测试的唯一标识，用于生成不重复的测试数据。"""
        return self._unique_id

    # ===== HTTP 请求方法 =====

    def request(
        self,
        method: str,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        authenticated: bool = True,
        timeout: float | None = None,
    ) -> httpx.Response:
        """发送 HTTP 请求。

        Args:
            method: HTTP 方法（GET, POST, PUT, DELETE, PATCH）
            url: 请求路径（相对于 BASE_URL）
            json: JSON 请求体
            data: 表单数据
            params: 查询参数
            headers: 额外的请求头
            authenticated: 是否携带认证信息（默认 True）
            timeout: 超时时间（秒）

        Returns:
            httpx.Response 响应对象
        """
        # 合并请求头
        merged_headers = {**self.DEFAULT_HEADERS}
        if headers:
            merged_headers.update(headers)

        # 替换 URL 中的变量引用
        url = self._resolve_variables(url)

        with allure.step(f"{method} {url}"):
            logger.info(f"发送请求: {method} {url}")
            if json:
                logger.debug(f"请求体: {json}")

            start_time = time.monotonic()
            response = self._client.request(
                method=method,
                url=url,
                json=json,
                data=data,
                params=params,
                headers=merged_headers,
                timeout=timeout or self.DEFAULT_TIMEOUT,
            )
            self._last_response_time = (time.monotonic() - start_time) * 1000

            logger.info(f"响应状态: {response.status_code}，耗时: {self._last_response_time:.0f}ms")

            # 记录到 Allure 报告
            allure.attach(
                response.text,
                name="响应体",
                attachment_type=allure.attachment_type.JSON,
            )

        return response

    # ===== 标准断言方法 =====

    def assert_status(self, response: httpx.Response, expected: int) -> None:
        """断言 HTTP 状态码。

        Args:
            response: HTTP 响应对象
            expected: 期望的状态码
        """
        with allure.step(f"断言状态码 == {expected}"):
            actual = response.status_code
            assert actual == expected, f"状态码不匹配：期望 {expected}，实际 {actual}\n响应体: {response.text[:500]}"

    def assert_json_field(
        self,
        response: httpx.Response,
        jsonpath_expr: str,
        *,
        expected: Any = None,
        exists: bool | None = None,
        type_is: type | None = None,
    ) -> None:
        """断言 JSON 响应体中的字段。

        Args:
            response: HTTP 响应对象
            jsonpath_expr: JSONPath 表达式
            expected: 期望的字段值
            exists: 断言字段是否存在（True/False）
            type_is: 断言字段的类型
        """
        body = response.json()
        matches = jsonpath_parse(jsonpath_expr).find(body)

        with allure.step(f"断言 JSON 字段: {jsonpath_expr}"):
            if exists is not None:
                if exists:
                    assert len(matches) > 0, f"字段不存在: {jsonpath_expr}\n响应体: {body}"
                else:
                    assert len(matches) == 0, f"字段不应存在但存在: {jsonpath_expr}\n响应体: {body}"
                return

            assert len(matches) > 0, f"字段不存在: {jsonpath_expr}\n响应体: {body}"
            actual = matches[0].value

            if expected is not None:
                assert actual == expected, f"字段值不匹配: {jsonpath_expr}\n期望: {expected}\n实际: {actual}"

            if type_is is not None:
                assert isinstance(actual, type_is), (
                    f"字段类型不匹配: {jsonpath_expr}\n期望类型: {type_is.__name__}\n实际类型: {type(actual).__name__}"
                )

    def assert_json_match(
        self,
        response: httpx.Response,
        jsonpath_expr: str,
        *,
        pattern: str,
    ) -> None:
        """断言 JSON 字段值匹配正则表达式。

        Args:
            response: HTTP 响应对象
            jsonpath_expr: JSONPath 表达式
            pattern: 正则表达式模式
        """
        body = response.json()
        matches = jsonpath_parse(jsonpath_expr).find(body)

        with allure.step(f"断言 JSON 字段匹配模式: {jsonpath_expr} =~ {pattern}"):
            assert len(matches) > 0, f"字段不存在: {jsonpath_expr}"
            actual = str(matches[0].value)
            assert re.search(pattern, actual), f"字段值不匹配模式: {jsonpath_expr}\n模式: {pattern}\n实际值: {actual}"

    def assert_json_length(
        self,
        response: httpx.Response,
        jsonpath_expr: str,
        *,
        expected: int | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
    ) -> None:
        """断言 JSON 数组长度。

        Args:
            response: HTTP 响应对象
            jsonpath_expr: JSONPath 表达式（指向数组）
            expected: 期望的精确长度
            min_length: 最小长度
            max_length: 最大长度
        """
        body = response.json()
        matches = jsonpath_parse(jsonpath_expr).find(body)

        with allure.step(f"断言 JSON 数组长度: {jsonpath_expr}"):
            assert len(matches) > 0, f"字段不存在: {jsonpath_expr}"
            actual_list = matches[0].value
            assert isinstance(actual_list, list), f"字段不是数组: {jsonpath_expr}"

            actual_len = len(actual_list)
            if expected is not None:
                assert actual_len == expected, f"数组长度不匹配: 期望 {expected}，实际 {actual_len}"
            if min_length is not None:
                assert actual_len >= min_length, f"数组长度不足: 最小 {min_length}，实际 {actual_len}"
            if max_length is not None:
                assert actual_len <= max_length, f"数组长度超限: 最大 {max_length}，实际 {actual_len}"

    def assert_json_contains(
        self,
        response: httpx.Response,
        jsonpath_expr: str,
        *,
        item: Any,
    ) -> None:
        """断言 JSON 数组包含指定元素。

        Args:
            response: HTTP 响应对象
            jsonpath_expr: JSONPath 表达式（指向数组）
            item: 期望包含的元素
        """
        body = response.json()
        matches = jsonpath_parse(jsonpath_expr).find(body)

        with allure.step(f"断言 JSON 数组包含: {item}"):
            assert len(matches) > 0, f"字段不存在: {jsonpath_expr}"
            actual_list = matches[0].value
            assert item in actual_list, f"数组不包含 {item}: {actual_list}"

    def assert_response_time(self, response: httpx.Response, *, max_ms: float) -> None:
        """断言响应时间。

        Args:
            response: HTTP 响应对象（未使用，保持接口一致性）
            max_ms: 最大允许的响应时间（毫秒）
        """
        with allure.step(f"断言响应时间 <= {max_ms}ms"):
            assert self._last_response_time <= max_ms, f"响应时间超标: {self._last_response_time:.0f}ms > {max_ms}ms"

    # ===== 变量提取方法 =====

    def extract_json(self, response: httpx.Response, jsonpath_expr: str) -> Any:
        """从 JSON 响应体中提取值。

        Args:
            response: HTTP 响应对象
            jsonpath_expr: JSONPath 表达式

        Returns:
            提取到的值
        """
        body = response.json()
        matches = jsonpath_parse(jsonpath_expr).find(body)
        assert len(matches) > 0, f"提取失败，字段不存在: {jsonpath_expr}\n响应体: {body}"
        value = matches[0].value
        logger.info(f"提取变量: {jsonpath_expr} = {value}")
        return value

    def extract_header(self, response: httpx.Response, header_name: str) -> str:
        """从响应头中提取值。

        Args:
            response: HTTP 响应对象
            header_name: 响应头名称

        Returns:
            响应头的值
        """
        value = response.headers.get(header_name)
        assert value is not None, f"响应头不存在: {header_name}"
        logger.info(f"提取响应头: {header_name} = {value}")
        return value

    def extract_regex(self, response: httpx.Response, pattern: str, group: int = 1) -> str:
        """从响应体中使用正则表达式提取值。

        Args:
            response: HTTP 响应对象
            pattern: 正则表达式模式
            group: 捕获组索引

        Returns:
            匹配到的值
        """
        match = re.search(pattern, response.text)
        assert match is not None, f"正则匹配失败: {pattern}\n响应体: {response.text[:500]}"
        value = match.group(group)
        logger.info(f"正则提取: {pattern} = {value}")
        return value

    # ===== 变量池管理 =====

    def save(self, name: str, value: Any) -> None:
        """保存变量到变量池。

        Args:
            name: 变量名
            value: 变量值
        """
        self._variables[name] = value
        logger.debug(f"保存变量: {name} = {value}")

    def load(self, name: str) -> Any:
        """从变量池加载变量。

        Args:
            name: 变量名

        Returns:
            变量值

        Raises:
            KeyError: 变量不存在
        """
        assert name in self._variables, f"变量不存在: {name}，可用变量: {list(self._variables.keys())}"
        return self._variables[name]

    # ===== 数据库断言方法 =====

    def assert_db_record(
        self,
        sql: str,
        params: list[Any] | None = None,
        *,
        exists: bool = True,
    ) -> None:
        """断言数据库记录是否存在。

        Args:
            sql: SQL 查询语句
            params: 查询参数
            exists: 期望记录是否存在
        """
        with allure.step(f"断言数据库记录{'存在' if exists else '不存在'}"):
            # TODO: 实现数据库查询
            logger.warning("数据库断言尚未实现，跳过")

    def assert_db_field(
        self,
        sql: str,
        params: list[Any] | None = None,
        *,
        field: str,
        expected: Any,
    ) -> None:
        """断言数据库字段值。

        Args:
            sql: SQL 查询语句
            params: 查询参数
            field: 字段名
            expected: 期望值
        """
        with allure.step(f"断言数据库字段 {field} == {expected}"):
            # TODO: 实现数据库字段断言
            logger.warning("数据库字段断言尚未实现，跳过")

    def assert_db_count(
        self,
        sql: str,
        params: list[Any] | None = None,
        *,
        expected: int,
    ) -> None:
        """断言数据库记录数量。

        Args:
            sql: SQL COUNT 查询语句
            params: 查询参数
            expected: 期望的记录数
        """
        with allure.step(f"断言数据库记录数 == {expected}"):
            # TODO: 实现数据库计数断言
            logger.warning("数据库计数断言尚未实现，跳过")

    # ===== 内部方法 =====

    def _resolve_variables(self, text: str) -> str:
        """解析文本中的变量引用（${var_name} 格式）。"""

        def replacer(match: re.Match[str]) -> str:
            var_name = match.group(1)
            if var_name in self._variables:
                return str(self._variables[var_name])
            return match.group(0)

        return re.sub(r"\$\{(\w+)\}", replacer, text)
