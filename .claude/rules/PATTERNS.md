# 测试场景模式

## 模式 1：CRUD 生命周期

最常用的模式。当用户通过 HAR 文件提供了"创建"场景时，**必须** 建议补全完整的 CRUD 闭环。

### 完整 CRUD 流程
```
创建(POST) → 查询(GET) → 更新(PUT/PATCH) → 查询验证 → 删除(DELETE) → 查询确认已删除
```

### 模板结构
```python
@allure.epic("业务域")
@allure.feature("模块 CRUD")
class TestModuleCRUD(BaseAPITest):
    """模块增改查删完整场景。"""

    @allure.story("创建")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_01_create_resource_with_valid_data_returns_201(self):
        """创建资源：提交合法数据，期望返回 201。"""
        payload = {... }
        response = self.request("POST", "/api/resources", json=payload)
        self.assert_status(response, 201)
        resource_id = self.extract_json(response, "$.data.id")
        self.save("resource_id", resource_id)

    @allure.story("查询")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_02_get_resource_by_id_returns_detail(self):
        """查询资源：根据 ID 查询，验证返回数据与创建时一致。"""
        resource_id = self.load("resource_id")
        response = self.request("GET", f"/api/resources/{resource_id}")
        self.assert_status(response, 200)
        self.assert_json_field(response, "$.data.id", expected=resource_id)

    @allure.story("更新")
    @allure.severity(allure.severity_level.NORMAL)
    def test_03_update_resource_with_new_data_returns_200(self):
        """更新资源：修改名称字段，验证更新成功。"""
        resource_id = self.load("resource_id")
        response = self.request("PUT", f"/api/resources/{resource_id}", json={"name": "新名称"})
        self.assert_status(response, 200)

    @allure.story("查询")
    @allure.severity(allure.severity_level.NORMAL)
    def test_04_get_resource_after_update_returns_new_data(self):
        """验证更新：查询更新后的资源，确认字段已变更。"""
        resource_id = self.load("resource_id")
        response = self.request("GET", f"/api/resources/{resource_id}")
        self.assert_status(response, 200)
        self.assert_json_field(response, "$.data.name", expected="新名称")

    @allure.story("删除")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_05_delete_resource_returns_success(self):
        """删除资源：删除已创建的资源。"""
        resource_id = self.load("resource_id")
        response = self.request("DELETE", f"/api/resources/{resource_id}")
        self.assert_status(response, 200)

    @allure.story("查询")
    @allure.severity(allure.severity_level.NORMAL)
    def test_06_get_deleted_resource_returns_404(self):
        """验证删除：查询已删除的资源，期望返回 404。"""
        resource_id = self.load("resource_id")
        response = self.request("GET", f"/api/resources/{resource_id}")
        self.assert_status(response, 404)
```

## 模式 2：认证场景

```python
@allure.epic("系统安全")
@allure.feature("登录认证")
class TestAuth(BaseAPITest):
    """登录认证相关场景。"""

    def test_01_login_with_valid_credentials_returns_token(self):
        """正常登录：使用合法凭证，获取 token。"""
        ...

    def test_02_access_protected_api_with_token_returns_200(self):
        """携带 token 访问受保护接口，期望成功。"""
        ...

    def test_03_access_protected_api_without_token_returns_401(self):
        """不携带 token 访问受保护接口，期望 401。"""
        ...

    def test_04_access_with_expired_token_returns_401(self):
        """使用过期 token 访问，期望 401。"""
        ...

    def test_05_refresh_token_returns_new_token(self):
        """刷新 token，获取新的有效 token。"""
        ...
```

## 模式 3：异常/负面场景

对每个接口，至少覆盖以下异常分支：

| 异常类型 | 预期状态码 | 说明 |
|---------|----------|------|
| 必填参数缺失 | 400 | 去掉一个必填字段 |
| 参数格式错误 | 400 | 邮箱格式、手机号格式等 |
| 参数值超范围 | 400 | 超长字符串、负数等 |
| 资源不存在 | 404 | 查询不存在的 ID |
| 资源冲突 | 409 | 重复创建同名资源 |
| 未授权访问 | 401 | 不携带 token |
| 权限不足 | 403 | 普通用户访问管理接口 |

```python
@allure.feature("用户管理 - 异常场景")
class TestUserNegative(BaseAPITest):
    """用户管理异常场景覆盖。"""

    @allure.severity(allure.severity_level.MINOR)
    def test_01_create_user_without_name_returns_400(self):
        """缺少必填字段：不传 name，期望 400。"""
        response = self.request("POST", "/api/users", json={"email": "a@b.com"})
        self.assert_status(response, 400)
        self.assert_json_field(response, "$.message", exists=True)

    @allure.severity(allure.severity_level.MINOR)
    def test_02_create_user_with_invalid_email_returns_400(self):
        """邮箱格式错误：传入非法邮箱，期望 400。"""
        response = self.request("POST", "/api/users", json={"name": "test", "email": "not-email"})
        self.assert_status(response, 400)

    @allure.severity(allure.severity_level.MINOR)
    def test_03_get_nonexistent_user_returns_404(self):
        """查询不存在的用户：使用虚假 ID，期望 404。"""
        response = self.request("GET", "/api/users/999999999")
        self.assert_status(response, 404)

    @allure.severity(allure.severity_level.MINOR)
    def test_04_create_duplicate_user_returns_409(self):
        """重复创建：创建同名用户，期望 409。"""
        ...
```

## 模式 4：分页查询

```python
@allure.feature("用户管理 - 分页查询")
class TestUserPagination(BaseAPITest):
    """分页查询场景。"""

    def test_01_query_first_page_returns_default_page_size(self):
        """查询第一页：不传分页参数，使用默认分页。"""
        response = self.request("GET", "/api/users")
        self.assert_status(response, 200)
        self.assert_json_field(response, "$.data.total", exists=True)
        self.assert_json_field(response, "$.data.pageSize", exists=True)
        self.assert_json_length(response, "$.data.list", min_length=0)

    def test_02_query_with_page_size_returns_correct_count(self):
        """指定分页大小：传入 pageSize=5，验证返回数量。"""
        response = self.request("GET", "/api/users", params={"pageSize": 5, "pageNum": 1})
        self.assert_status(response, 200)
        self.assert_json_length(response, "$.data.list", max_length=5)

    def test_03_query_with_keyword_returns_filtered_results(self):
        """关键词搜索：传入搜索关键词，验证结果匹配。"""
        ...
```

## 模式 5：前置数据清理

对于需要特定数据状态的场景，使用 pre_sql 清理：

```python
class TestModuleScenario(BaseAPITest):
    """需要数据清理的场景。"""

    def test_01_setup_clean_data(self):
        """前置：清理测试数据，确保干净环境。"""
        self.execute_sql("DELETE FROM resources WHERE name LIKE 'test_%'")

    def test_02_actual_test_case(self):
        """实际测试用例。"""
        ...
```

## 查漏补缺规则

当用户提供 HAR 文件中只包含部分场景时，**必须** 建议补充：

1. **CRUD 闭环**：有创建必须有删除，有更新必须有查询验证
2. **异常覆盖**：每个接口至少覆盖 2-3 个异常分支
3. **权限校验**：涉及权限的接口必须测试无权限场景
4. **边界值**：字符串长度、数值范围、空值处理
5. **幂等性**：重复提交同一请求是否安全
