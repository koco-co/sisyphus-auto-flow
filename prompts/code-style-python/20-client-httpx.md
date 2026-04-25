# httpx 客户端规范

> 当 fingerprint.http_client.library == "httpx" 时加载

## 规则

1. 使用 `httpx.Client()` 作为上下文管理器
2. 使用 client.post/get/put/delete 发起请求

## 示例

```python
import httpx
with httpx.Client(base_url=BASE_URL) as client:
    resp = client.post("/api/endpoint", json={...})
```
