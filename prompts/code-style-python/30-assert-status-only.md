# status_code 断言规范

> 当 fingerprint.assertion.style 为 status_only 或 null 时加载

## 规则

1. 主要断言：`assert resp.status_code == 200`
2. 不使用业务码断言

## 示例

```python
assert resp.status_code == 200
```
