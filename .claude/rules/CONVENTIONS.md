# 代码规范

所有生成的测试代码 **必须** 严格遵守以下规范。

## 文件组织

### 文件命名
- 测试文件：`test_{模块}_{场景}.py`（例：`test_user_crud.py`、`test_order_auth.py`）
- 一个文件对应一个测试场景，不要把多个场景混在一起

### 类命名
- 测试类：`Test{模块}{场景}`（例：`TestUserCRUD`、`TestOrderAuth`）
- 每个文件只定义一个测试类

### 方法命名
- 格式：`test_{序号}_{动作}_{条件}_{预期结果}`
- 序号用两位数字：01、02、03...（保证执行顺序）
- 例：`test_01_create_user_with_valid_data_returns_201`
- 例：`test_02_query_user_by_id_returns_user_detail`
- 例：`test_03_update_user_with_invalid_email_returns_400`

## 导入顺序

```python
"""模块描述（中文）。"""

from __future__ import annotations

# 1. 标准库
import json

# 2. 第三方库
import allure
import pytest

# 3. 项目内部
from sisyphus_auto_flow.core.base import BaseAPITest
```

## 类结构

```python
@allure.epic("史诗名称")
@allure.feature("功能模块名称")
class TestModuleScenario(BaseAPITest):
    """场景描述（中文）。"""

    @allure.story("用户故事")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_01_action_condition_expected(self):
        """测试用例描述（中文）。"""
        # --- Arrange（准备数据）---
        payload = {...}

        # --- Act（执行操作）---
        response = self.request("POST", "/api/endpoint", json=payload)

        # --- Assert（验证结果）---
        self.assert_status(response, 201)
        self.assert_json_field(response, "$.data.id", exists=True)
```

## Allure 装饰器规则

| 装饰器 | 用途 | 示例 |
|--------|------|------|
| `@allure.epic()` | 业务域 | `"用户管理"`, `"订单系统"` |
| `@allure.feature()` | 功能模块 | `"用户 CRUD"`, `"登录认证"` |
| `@allure.story()` | 用户故事 | `"创建用户"`, `"查询用户列表"` |
| `@allure.severity()` | 优先级 | `BLOCKER > CRITICAL > NORMAL > MINOR > TRIVIAL` |

### 优先级使用规则
- `BLOCKER`：核心流程（登录、创建订单）
- `CRITICAL`：CRUD 基本操作
- `NORMAL`：常规查询、更新
- `MINOR`：边界条件、异常分支
- `TRIVIAL`：格式校验、默认值检查

## 注释与文档

- **所有注释和文档字符串必须使用中文**
- 模块级文档字符串：说明本文件覆盖的测试场景
- 类级文档字符串：说明场景的业务背景
- 方法级文档字符串：说明测试目的
- 行内注释：解释非显而易见的逻辑

## 变量传递

当一个测试方法的返回值需要在后续方法中使用时：
```python
# 提取变量
user_id = self.extract_json(response, "$.data.id")
self.save("user_id", user_id)

# 在后续方法中使用
user_id = self.load("user_id")
response = self.request("GET", f"/api/users/{user_id}")
```

## 禁止事项

- ❌ 不要硬编码环境地址（使用 config）
- ❌ 不要使用 `requests` 库（使用 `self.request()`）
- ❌ 不要使用 `assert` 原生语句（使用 `self.assert_*` 方法）
- ❌ 不要跳过测试序号（01→02→03，不要 01→03）
- ❌ 不要在测试方法中 print（使用 loguru）
- ❌ 不要使用英文注释
