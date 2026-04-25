# 多环境配置规范

> 当 fingerprint.env_management.detected == true 时加载

## 规则

1. Base URL 必须从环境的配置模块读取，不得硬编码
2. 使用 `ENV_CONF.base_url.{module}` 或等价方式获取 URL
3. 枚举值、数据库连接等环境相关配置也通过 ENV_CONF 获取

## 示例

```python
# 正确：从环境配置读取
from config.env_config import ENV_CONF
from api.batch.batch_api import BatchApi

url = ENV_CONF.base_url.rdos + BatchApi.create_project.value

# 错误：硬编码
url = "http://172.16.122.52:82" + "/api/rdos/..."
```

## 切换环境

用户通过 `.env` 文件或环境变量切换环境，测试代码无需修改。
