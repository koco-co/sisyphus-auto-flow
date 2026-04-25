# 内联 URL 规范

> 当 fingerprint.api.type 为 inline 或 null 时加载

## 规则

1. URL 可以硬编码为字符串
2. 从 HAR 中读取路径部分

## 示例

```python
url = base_url + "/api/rdos/common/project/createProject"
```
