# resp["code"] == 1 断言规范

> 当 fingerprint.assertion.style == "code_success" 时加载

## 规则

1. 主要断言：`assert resp["code"] == 1, resp["message"]`
2. 成功断言：`assert resp["success"] is True`
3. 若有 helper_methods（如 `assert_response_success`），优先使用辅助方法

## 示例

```python
resp = self.req.post(url, "创建资源", json=params)
assert resp["code"] == 1, resp["message"]
assert resp["success"] is True
```
