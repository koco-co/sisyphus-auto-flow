"""数据资产 — CRUD 闭环测试。"""

from __future__ import annotations

import allure
import pytest

from sisyphus_auto_flow.core.base import BaseAPITest
from testdata.assets.assets_crud_data import create_datasource_data, negative_datasource_data


@allure.epic("数据资产")
@allure.feature("数据源 CRUD")
@pytest.mark.live
class TestAssetsCRUD(BaseAPITest):
    """数据资产增删改查闭环测试。"""

    @allure.story("创建数据源")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("data", create_datasource_data, ids=lambda d: d["case"])
    def test_01_create_datasource_with_valid_data_returns_200(self, data: dict) -> None:
        """正向：使用有效数据创建数据源。"""
        # Arrange
        payload = {
            "source_type": data["source_type"],
            "datasource_name": f"{data['datasource_name']}_{self.unique_id}",
            "db_name": data["db_name"],
        }

        # Act
        response = self.request("POST", "/dassets/v1/dataDb/batchAddDb", json=payload)

        # Assert
        self.assert_status(response, data["expected_status"])
        self.assert_json_field(response, "$.data.id", exists=True)
        self.save("datasource_id", self.extract_json(response, "$.data.id"))

    @allure.story("查询数据源")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_02_query_datasource_returns_200(self) -> None:
        """正向：查询已创建的数据源。"""
        # Act
        response = self.request("GET", "/dassets/v1/dataDb/pageQuery", params={"pageSize": 10})

        # Assert
        self.assert_status(response, 200)
        self.assert_json_field(response, "$.data.totalCount", exists=True)

    @allure.story("异常场景")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize("data", negative_datasource_data, ids=lambda d: d["case"])
    def test_03_create_datasource_with_invalid_data(self, data: dict) -> None:
        """异常：使用无效数据创建数据源，验证错误处理。"""
        # Arrange
        payload = {"source_type": data["source_type"], "datasource_name": data["datasource_name"]}

        # Act
        response = self.request("POST", "/dassets/v1/dataDb/batchAddDb", json=payload)

        # Assert
        self.assert_status(response, data["expected_status"])
