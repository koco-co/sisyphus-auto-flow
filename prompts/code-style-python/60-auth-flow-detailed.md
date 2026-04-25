# 多步认证流程规范

> 当 fingerprint.auth.flow 存在且包含多个步骤时加载

## 规则

1. 测试代码应复用项目已有的认证类，而非自行实现认证
2. 在测试类的 `setup_class` 或会话 fixture 中实例化认证类
3. 若认证类自动在 HTTP 客户端构造时注入，测试代码无需额外处理

## 示例

```python
# 认证已由 BaseRequests.__init__ 自动处理
from utils.common.BaseRequests import BaseRequests

class TestFeature:
    def setup_class(self):
        self.req = BaseRequests()  # 自动注入 cookie

    def test_something(self):
        resp = self.req.post(url, "描述", json={...})
```

## 凭证来源

认证凭据从 ENV_CONF 或 .env 读取，测试代码不应包含明文凭据。
