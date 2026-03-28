# 数据库断言规范

## 何时使用数据库断言

| 操作类型 | 是否需要数据库断言 | 说明 |
|---------|------------------|------|
| 创建（POST） | ✅ 必须 | 验证记录已正确写入 |
| 更新（PUT/PATCH） | ✅ 必须 | 验证字段已正确更新 |
| 删除（DELETE） | ✅ 必须 | 验证记录已删除（逻辑/物理） |
| 查询（GET） | ❌ 通常不需要 | 响应体断言已足够 |

## 前置数据清理（pre_sql）

在测试开始前清理可能存在的脏数据：

```python
def test_01_setup_clean_environment(self):
    """前置：清理测试残留数据。"""
    # 清理上次测试可能残留的数据
    self.execute_sql(
        "DELETE FROM users WHERE name LIKE %s",
        params=["autotest_%"],
    )
    self.execute_sql(
        "DELETE FROM orders WHERE user_id IN (SELECT id FROM users WHERE name LIKE %s)",
        params=["autotest_%"],
    )
```

### 清理规则
- 使用 `autotest_` 前缀标记测试数据，方便清理
- 先清理子表（外键依赖），再清理主表
- 使用参数化查询，**禁止** 拼接 SQL

## 创建后验证（post_sql）

```python
def test_02_create_user_and_verify_db(self):
    """创建用户后验证数据库记录。"""
    # --- Act ---
    response = self.request("POST", "/api/users", json={
        "name": "autotest_张三",
        "email": "zhangsan@test.com",
    })
    self.assert_status(response, 201)
    user_id = self.extract_json(response, "$.data.id")
    self.save("user_id", user_id)

    # --- 数据库断言 ---
    # 验证记录存在
    self.assert_db_record(
        "SELECT * FROM users WHERE id = %s",
        params=[user_id],
        exists=True,
    )
    # 验证具体字段值
    self.assert_db_field(
        "SELECT name, email, status FROM users WHERE id = %s",
        params=[user_id],
        field="name",
        expected="autotest_张三",
    )
    self.assert_db_field(
        "SELECT name, email, status FROM users WHERE id = %s",
        params=[user_id],
        field="status",
        expected=1,  # 默认状态：启用
    )
```

## 更新后验证

```python
def test_04_update_user_and_verify_db(self):
    """更新用户后验证数据库字段变更。"""
    user_id = self.load("user_id")

    # --- Act ---
    response = self.request("PUT", f"/api/users/{user_id}", json={
        "name": "autotest_李四",
    })
    self.assert_status(response, 200)

    # --- 数据库断言 ---
    self.assert_db_field(
        "SELECT name FROM users WHERE id = %s",
        params=[user_id],
        field="name",
        expected="autotest_李四",
    )
```

## 删除后验证

```python
def test_06_delete_user_and_verify_db(self):
    """删除用户后验证数据库状态。"""
    user_id = self.load("user_id")

    # --- Act ---
    response = self.request("DELETE", f"/api/users/{user_id}")
    self.assert_status(response, 200)

    # --- 逻辑删除验证 ---
    self.assert_db_field(
        "SELECT is_deleted FROM users WHERE id = %s",
        params=[user_id],
        field="is_deleted",
        expected=1,
    )

    # --- 物理删除验证（二选一） ---
    # self.assert_db_record(
    #     "SELECT * FROM users WHERE id = %s",
    #     params=[user_id],
    #     exists=False,
    # )
```

## 记录数量验证

```python
# 验证创建后记录数增加
self.assert_db_count(
    "SELECT COUNT(*) as cnt FROM users WHERE status = 1",
    field="cnt",
    expected=original_count + 1,
)

# 验证批量操作影响的记录数
self.assert_db_count(
    "SELECT COUNT(*) as cnt FROM users WHERE name LIKE %s",
    params=["autotest_%"],
    field="cnt",
    expected=3,
)
```

## SQL 编写规范

1. **参数化查询**：使用 `%s` 占位符 + `params` 列表，禁止字符串拼接
2. **测试数据前缀**：所有测试创建的数据使用 `autotest_` 前缀
3. **字段明确**：`SELECT` 明确列出需要的字段，避免 `SELECT *`（COUNT 除外）
4. **表名规范**：使用实际表名，不要使用别名

## 数据清理策略

### 方式一：前置清理（推荐）
在测试场景的第一个方法中清理数据，保证环境干净。

### 方式二：后置清理
在测试场景的最后一个方法中清理数据。

### 方式三：fixture 清理
使用 `cleanup` fixture 注册清理回调：
```python
def test_01_create_with_cleanup(self, cleanup):
    """创建资源并注册清理。"""
    response = self.request("POST", "/api/users", json={...})
    user_id = self.extract_json(response, "$.data.id")

    # 注册清理：测试结束后自动执行
    cleanup.register_sql("DELETE FROM users WHERE id = %s", params=[user_id])
```
