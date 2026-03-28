"""元数据中心 API 端点定义。"""

from __future__ import annotations

from enum import StrEnum


class MetadataApi(StrEnum):
    """元数据中心接口端点注册表。"""

    sync_task_page_task = "/dmetadata/v1/syncTask/pageTask"
    sync_task_real_time_table_list = "/dmetadata/v1/syncTask/realTimeTableList"
    sync_task_add = "/dmetadata/v1/syncTask/add"

    data_source_list_metadata_datasource = "/dmetadata/v1/dataSource/listMetadataDataSource"
    data_db_real_time_db_list = "/dmetadata/v1/dataDb/realTimeDbList"

    metadata_apply_is_super_user = "/dmetadata/v1/metadataApply/isSuperUser"
    metadata_apply_get_apply_status = "/dmetadata/v1/metadataApply/getApplyStatus"

    data_table_get_table_life_cycle = "/dmetadata/v1/dataTable/getTableLifeCycle"
    data_table_query_table_permission = "/dmetadata/v1/dataTable/queryTablePermission"

    data_subscribe_get_subscribe_by_table_id = "/dmetadata/v1/dataSubscribe/getSubscribeByTableId"
