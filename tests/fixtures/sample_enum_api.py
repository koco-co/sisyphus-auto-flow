from enum import Enum


class BatchApi(Enum):
    get_task = "/api/rdos/batch/batchTask/getTaskById"
    add_task = "/api/rdos/batch/batchTask/addOrUpdateTask"
    delete_task = "/api/rdos/batch/batchTask/deleteTask"


class AssetsApi(Enum):
    list_assets = "/dassets/v1/assets/list"
