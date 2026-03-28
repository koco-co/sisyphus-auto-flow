"""数据资产 CRUD 测试数据。

测试数据与测试逻辑分离，供 @pytest.mark.parametrize 使用。
数据文件命名规则：{module}_{scenario}_data.py
"""

from __future__ import annotations

# 创建数据源的参数化测试数据
create_datasource_data = [
    {
        "case": "MySQL 数据源",
        "source_type": "MySQL",
        "datasource_name": "auto_mysql_default",
        "db_name": "automation",
        "expected_status": 200,
    },
    {
        "case": "Hive 数据源",
        "source_type": "Hive",
        "datasource_name": "auto_hive_default",
        "db_name": "default",
        "expected_status": 200,
    },
]

# 异常场景数据
negative_datasource_data = [
    {
        "case": "空数据源名称",
        "source_type": "MySQL",
        "datasource_name": "",
        "expected_status": 400,
        "expected_message": "数据源名称不能为空",
    },
    {
        "case": "不存在的数据源类型",
        "source_type": "NonExistent",
        "datasource_name": "auto_test",
        "expected_status": 400,
        "expected_message": "不支持的数据源类型",
    },
]
