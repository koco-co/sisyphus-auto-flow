# 自定义 HTTP 客户端调用规范

> 当 fingerprint.http_client.client_pattern == "custom_class" 时加载

## 规则

1. 在 `setup_class` 中实例化：`self.client = {ClassName}()`
2. 调用方法签名匹配检测到的签名：`self.client.{method}(url, desc, **kwargs)`
3. 不使用 httpx/requests 裸调用

## 示例

```python
from utils.common.BaseRequests import BaseRequests

class TestCreateProject:
    def setup_class(self):
        self.req = BaseRequests()

    def test_create_project(self):
        resp = self.req.post(url, "新建项目", json=params)
```

若 fingerprint.allure.attach_on_request 为 true，自定义客户端已自动处理 allure attach，不需在测试方法中手动 attach。
