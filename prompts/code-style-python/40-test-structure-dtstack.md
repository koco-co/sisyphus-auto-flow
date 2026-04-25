# dtstack 风格测试结构

> 当 fingerprint.test_style.file_suffix == "*_test.py" 时加载

## 规则

1. 测试文件以 `_test.py` 结尾
2. 测试类包含 `setup_class` 方法
3. 类 docstring 格式：`"""测试-{序号} {描述}"""`
4. 使用项目已注册的 pytest markers（如 @pytest.mark.smoke）

## 示例

```python
@pytest.mark.smoke
class TestCreateProject:
    """测试-1 新建项目"""

    def setup_class(self):
        self.req = BaseRequests()

    def test_create_project(self):
        ...
```
