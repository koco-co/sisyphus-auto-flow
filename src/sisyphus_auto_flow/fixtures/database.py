"""数据库连接和断言 pytest fixtures。

提供 MySQL 数据库连接、查询、断言功能。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pymysql
import pytest
from loguru import logger

if TYPE_CHECKING:
    from collections.abc import Generator


class DatabaseHelper:
    """数据库操作辅助类。"""

    def __init__(self, connection: pymysql.Connection) -> None:  # type: ignore[type-arg]
        self._conn = connection

    def execute(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> int:
        """执行 SQL（INSERT/UPDATE/DELETE），返回影响行数。"""
        with self._conn.cursor() as cursor:
            count = cursor.execute(sql, params)
            self._conn.commit()
            logger.debug(f"SQL 执行完成，影响 {count} 行: {sql}")
            return count

    def fetch_one(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> dict[str, Any] | None:
        """查询单条记录。"""
        with self._conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()

    def fetch_all(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
        """查询多条记录。"""
        with self._conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())

    def count(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> int:
        """执行 COUNT 查询，返回记录数。"""
        with self._conn.cursor() as cursor:
            cursor.execute(sql, params)
            result = cursor.fetchone()
            return result[0] if result else 0


@pytest.fixture(scope="session")
def db_connection(env_config: dict[str, Any]) -> Generator[pymysql.Connection]:  # type: ignore[type-arg]
    """创建数据库连接（会话级别）。"""
    db_cfg = env_config.get("database", {})
    if not db_cfg:
        pytest.skip("未配置数据库连接信息")

    conn = pymysql.connect(
        host=db_cfg.get("host", "localhost"),
        port=db_cfg.get("port", 3306),
        user=db_cfg.get("user", "root"),
        password=db_cfg.get("password", ""),
        database=db_cfg.get("database", "test"),
        charset=db_cfg.get("charset", "utf8mb4"),
        autocommit=False,
    )
    logger.info(f"数据库连接成功: {db_cfg.get('host')}:{db_cfg.get('port')}/{db_cfg.get('database')}")
    yield conn
    conn.close()
    logger.info("数据库连接已关闭")


@pytest.fixture
def db(db_connection: pymysql.Connection) -> DatabaseHelper:  # type: ignore[type-arg]
    """获取数据库操作辅助实例。"""
    return DatabaseHelper(db_connection)
