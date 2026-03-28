# 完整示例

## 示例 1：用户 CRUD 完整场景（含数据库断言）

```python
"""用户管理 CRUD 完整测试场景。

覆盖用户的创建、查询、更新、删除全生命周期，
包含数据库断言验证数据一致性。
"""

from __future__ import annotations

import allure

from sisyphus_auto_flow.core.base import BaseAPITest


@allure.epic("用户管理")
@allure.feature("用户 CRUD")
class TestUserCRUD(BaseAPITest):
    """用户增改查删完整场景。"""

    @allure.story("前置清理")
    @allure.severity(allure.severity_level.NORMAL)
    def test_01_cleanup_test_data(self):
        """前置：清理历史测试数据，确保环境干净。"""
        self.execute_sql(
            "DELETE FROM users WHERE name LIKE %s",
            params=["autotest_%"],
        )

    @allure.story("创建用户")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_02_create_user_with_valid_data_returns_201(self):
        """创建用户：提交合法数据，期望返回 201 并生成用户 ID。"""
        # --- Arrange ---
        payload = {
            "name": "autotest_张三",
            "email": "zhangsan@autotest.com",
            "phone": "13800138000",
            "role": "user",
        }

        # --- Act ---
        response = self.request("POST", "/api/v1/users", json=payload)

        # --- Assert ---
        self.assert_status(response, 201)
        self.assert_json_field(response, "$.data.id", exists=True)
        self.assert_json_field(response, "$.data.name", expected="autotest_张三")

        # 提取变量供后续使用
        user_id = self.extract_json(response, "$.data.id")
        self.save("user_id", user_id)

        # 数据库断言：验证记录已写入
        self.assert_db_record(
            "SELECT id, name, email FROM users WHERE id = %s",
            params=[user_id],
            exists=True,
        )
        self.assert_db_field(
            "SELECT name FROM users WHERE id = %s",
            params=[user_id],
            field="name",
            expected="autotest_张三",
        )

    @allure.story("查询用户")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_03_get_user_by_id_returns_detail(self):
        """查询用户：根据 ID 查询用户详情，验证数据一致性。"""
        user_id = self.load("user_id")

        response = self.request("GET", f"/api/v1/users/{user_id}")

        self.assert_status(response, 200)
        self.assert_json_match(response, {
            "$.data.id": user_id,
            "$.data.name": "autotest_张三",
            "$.data.email": "zhangsan@autotest.com",
        })

    @allure.story("更新用户")
    @allure.severity(allure.severity_level.NORMAL)
    def test_04_update_user_name_returns_200(self):
        """更新用户：修改用户名称，验证更新成功。"""
        user_id = self.load("user_id")

        response = self.request("PUT", f"/api/v1/users/{user_id}", json={
            "name": "autotest_李四",
        })

        self.assert_status(response, 200)
        self.assert_json_field(response, "$.data.name", expected="autotest_李四")

        # 数据库断言：验证已更新
        self.assert_db_field(
            "SELECT name FROM users WHERE id = %s",
            params=[user_id],
            field="name",
            expected="autotest_李四",
        )

    @allure.story("查询用户")
    @allure.severity(allure.severity_level.NORMAL)
    def test_05_get_user_after_update_returns_new_data(self):
        """验证更新：查询更新后的用户，确认名称已变更。"""
        user_id = self.load("user_id")

        response = self.request("GET", f"/api/v1/users/{user_id}")

        self.assert_status(response, 200)
        self.assert_json_field(response, "$.data.name", expected="autotest_李四")

    @allure.story("删除用户")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_06_delete_user_returns_200(self):
        """删除用户：删除已创建的用户。"""
        user_id = self.load("user_id")

        response = self.request("DELETE", f"/api/v1/users/{user_id}")

        self.assert_status(response, 200)

        # 数据库断言：验证已逻辑删除
        self.assert_db_field(
            "SELECT is_deleted FROM users WHERE id = %s",
            params=[user_id],
            field="is_deleted",
            expected=1,
        )

    @allure.story("查询用户")
    @allure.severity(allure.severity_level.NORMAL)
    def test_07_get_deleted_user_returns_404(self):
        """验证删除：查询已删除的用户，期望返回 404。"""
        user_id = self.load("user_id")

        response = self.request("GET", f"/api/v1/users/{user_id}")

        self.assert_status(response, 404)
```

## 示例 2：异常场景覆盖

```python
"""用户管理异常场景测试。

覆盖参数校验、权限控制、资源冲突等异常分支。
"""

from __future__ import annotations

import allure

from sisyphus_auto_flow.core.base import BaseAPITest


@allure.epic("用户管理")
@allure.feature("用户管理 - 异常场景")
class TestUserNegative(BaseAPITest):
    """用户管理异常场景覆盖。"""

    @allure.story("参数校验")
    @allure.severity(allure.severity_level.MINOR)
    def test_01_create_user_without_required_field_returns_400(self):
        """必填字段缺失：不传 name 字段，期望 400。"""
        response = self.request("POST", "/api/v1/users", json={
            "email": "test@autotest.com",
        })

        self.assert_status(response, 400)
        self.assert_json_field(response, "$.message", exists=True)

    @allure.story("参数校验")
    @allure.severity(allure.severity_level.MINOR)
    def test_02_create_user_with_invalid_email_returns_400(self):
        """邮箱格式错误：传入非法邮箱格式，期望 400。"""
        response = self.request("POST", "/api/v1/users", json={
            "name": "autotest_error",
            "email": "not-a-valid-email",
        })

        self.assert_status(response, 400)

    @allure.story("参数校验")
    @allure.severity(allure.severity_level.MINOR)
    def test_03_create_user_with_too_long_name_returns_400(self):
        """名称超长：传入超过限制长度的名称，期望 400。"""
        response = self.request("POST", "/api/v1/users", json={
            "name": "a" * 256,
            "email": "long@autotest.com",
        })

        self.assert_status(response, 400)

    @allure.story("资源不存在")
    @allure.severity(allure.severity_level.MINOR)
    def test_04_get_nonexistent_user_returns_404(self):
        """查询不存在的用户：使用虚假 ID，期望 404。"""
        response = self.request("GET", "/api/v1/users/999999999")

        self.assert_status(response, 404)

    @allure.story("资源不存在")
    @allure.severity(allure.severity_level.MINOR)
    def test_05_update_nonexistent_user_returns_404(self):
        """更新不存在的用户：期望 404。"""
        response = self.request("PUT", "/api/v1/users/999999999", json={
            "name": "ghost",
        })

        self.assert_status(response, 404)

    @allure.story("资源不存在")
    @allure.severity(allure.severity_level.MINOR)
    def test_06_delete_nonexistent_user_returns_404(self):
        """删除不存在的用户：期望 404。"""
        response = self.request("DELETE", "/api/v1/users/999999999")

        self.assert_status(response, 404)

    @allure.story("权限控制")
    @allure.severity(allure.severity_level.NORMAL)
    def test_07_access_without_token_returns_401(self):
        """无 token 访问：不携带 Authorization 头，期望 401。"""
        response = self.request(
            "GET", "/api/v1/users",
            headers={"Authorization": ""},
        )

        self.assert_status(response, 401)
```

## 示例 3：认证场景

```python
"""登录认证完整测试场景。

覆盖正常登录、token 刷新、权限校验、异常登录等场景。
"""

from __future__ import annotations

import allure

from sisyphus_auto_flow.core.base import BaseAPITest


@allure.epic("系统安全")
@allure.feature("登录认证")
class TestLoginAuth(BaseAPITest):
    """登录认证完整场景。"""

    @allure.story("正常登录")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_01_login_with_valid_credentials_returns_token(self):
        """正常登录：使用合法账号密码，期望返回 token。"""
        response = self.request("POST", "/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123",
        })

        self.assert_status(response, 200)
        self.assert_json_field(response, "$.data.token", exists=True)

        # 保存 token 供后续使用
        token = self.extract_json(response, "$.data.token")
        self.save("auth_token", token)

    @allure.story("Token 验证")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_02_access_with_valid_token_returns_200(self):
        """携带有效 token：访问受保护接口，期望 200。"""
        token = self.load("auth_token")

        response = self.request(
            "GET", "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assert_status(response, 200)
        self.assert_json_field(response, "$.data.username", expected="admin")

    @allure.story("异常登录")
    @allure.severity(allure.severity_level.NORMAL)
    def test_03_login_with_wrong_password_returns_401(self):
        """密码错误：使用错误密码登录，期望 401。"""
        response = self.request("POST", "/api/v1/auth/login", json={
            "username": "admin",
            "password": "wrong_password",
        })

        self.assert_status(response, 401)
        self.assert_json_field(response, "$.message", exists=True)

    @allure.story("异常登录")
    @allure.severity(allure.severity_level.NORMAL)
    def test_04_login_with_nonexistent_user_returns_401(self):
        """用户不存在：使用不存在的用户名登录，期望 401。"""
        response = self.request("POST", "/api/v1/auth/login", json={
            "username": "nonexistent_user",
            "password": "any_password",
        })

        self.assert_status(response, 401)

    @allure.story("异常登录")
    @allure.severity(allure.severity_level.MINOR)
    def test_05_login_without_password_returns_400(self):
        """缺少密码：只传用户名不传密码，期望 400。"""
        response = self.request("POST", "/api/v1/auth/login", json={
            "username": "admin",
        })

        self.assert_status(response, 400)
```
