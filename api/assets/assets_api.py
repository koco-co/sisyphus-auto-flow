"""数据资产 API 端点定义。

所有数据资产相关的接口 URL 集中注册在此。
测试用例通过引用枚举值获取接口路径，避免硬编码。
"""

from __future__ import annotations

from enum import StrEnum


class AssetsApi(StrEnum):
    """数据资产接口端点注册表。"""

    # 数据地图
    data_search_datasource_list = "/dassets/v1/dataSearch/datasourceList"
    data_search_db_list = "/dassets/v1/dataSearch/dblist"
    data_search_list_filters = "/dassets/v1/dataSearch/listFilters"

    # 数据表管理
    data_table_preview_data = "/dassets/v1/dataTable/previewData"
    data_table_version_compare = "/dassets/v1/dataTable/tableVersionCompare"

    # 数据表字段
    data_table_column_get_columns = "/dassets/v1/dataTableColumn/getColumns"
    data_table_column_get_by_table_id = "/dassets/v1/dataTableColumn/getColumnsByTableId"

    # 元数据
    metadata_fill_rate_by_database = "/dassets/v1/metaDataValid/fillRateByDatabase"
    model_attribute_get_column_header = "/dassets/v1/modelAttribute/getColumnHeader"

    # 血缘
    lineage_save_table = "/dassets/v1/lineage/saveTable"
    lineage_list_unused_db = "/dassets/v1/lineage/listUnusedDb"

    # 数据源
    data_db_batch_add = "/dassets/v1/dataDb/batchAddDb"
    data_db_page_query = "/dassets/v1/dataDb/pageQuery"

    # 同步任务
    sync_job_get_sync_log = "/dassets/v1/syncJob/getSyncLog"
    schedule_job_save_today_preview = "/dassets/v1/scheduleJob/saveTodayPreviewData"

    # 资源目录
    resource_catalog_list = "/dassets/v1/resourceCatalog/listCatalog"
