# Enum 风格 API 规范

> 当 fingerprint.api.type == "enum" 时加载

## 规则

1. URL 必须通过 `{EnumClass}.{member}.value` 引用，不得硬编码字符串
2. 完整 URL 为 `{base_url}{EnumClass.{member}.value}`

## 示例

```python
from api.batch.batch_api import BatchApi
url = base_url + BatchApi.create_project.value
```
