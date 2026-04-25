# requests 客户端规范

> 当 fingerprint.http_client.library == "requests" 时加载

## 规则

1. 使用 `requests.session()` 或裸 `requests.post/get`
2. 考虑添加超时设置

## 示例

```python
import requests
resp = requests.post(url, json=params, timeout=30)
```
