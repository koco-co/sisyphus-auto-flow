# Class 风格 API 规范

> 当 fingerprint.api.type == "class" 时加载

## 规则

1. URL 定义在类的 static/classmethod 中
2. 通过 `{Class}.{method}()` 获取 URL

## 示例

```python
class BatchApi:
    @staticmethod
    def create_project(): return "/api/rdos/common/project/createProject"
```
