# 断言规范

## 断言优先级

对每个 API 响应，**必须** 按以下优先级顺序进行断言：

1. **HTTP 状态码**（必须，永远第一个）
2. **响应体结构**（必填字段是否存在）
3. **响应体值**（具体字段值是否正确）
4. **数据库状态**（如适用：记录是否正确写入/更新/删除）
5. **响应时间**（如有 SLA 要求）

## 状态码断言

```python
# 基本状态码断言
self.assert_status(response, 200)
self.assert_status(response, 201)  # 创建成功
self.assert_status(response, 204)  # 删除成功（无内容）

# 错误状态码
self.assert_status(response, 400)  # 参数错误
self.assert_status(response, 401)  # 未授权
self.assert_status(response, 403)  # 无权限
self.assert_status(response, 404)  # 资源不存在
self.assert_status(response, 409)  # 资源冲突（重复创建）
```

## 响应体结构断言

验证必填字段是否存在：

```python
# 验证字段存在
self.assert_json_field(response, "$.data.id", exists=True)
self.assert_json_field(response, "$.data.name", exists=True)

# 验证嵌套结构
self.assert_json_field(response, "$.data.creator.id", exists=True)
```

## 响应体值断言

验证具体字段值：

```python
# 精确匹配
self.assert_json_field(response, "$.data.name", expected="张三")
self.assert_json_field(response, "$.data.status", expected=1)
self.assert_json_field(response, "$.data.is_active", expected=True)

# 批量匹配
self.assert_json_match(response, {
    "$.data.name": "张三",
    "$.data.email": "zhangsan@example.com",
    "$.data.role": "admin",
})

# 列表长度
self.assert_json_length(response, "$.data.list", min_length=1)
self.assert_json_length(response, "$.data.list", expected_length=10)

# 包含检查
self.assert_json_contains(response, "$.data.tags", "重要")
```

## 数据库断言

在涉及数据变更的操作后验证数据库状态：

```python
# 验证记录存在
self.assert_db_record(
    "SELECT * FROM users WHERE id = %s",
    params=[user_id],
    exists=True,
)

# 验证字段值
self.assert_db_field(
    "SELECT name, email FROM users WHERE id = %s",
    params=[user_id],
    field="name",
    expected="张三",
)

# 验证记录数量
self.assert_db_count(
    "SELECT COUNT(*) as cnt FROM users WHERE status = 1",
    field="cnt",
    expected=5,
)
```

## 响应时间断言

```python
# 单次请求耗时
self.assert_response_time(response, max_ms=2000)

# 严格 SLA
self.assert_response_time(response, max_ms=500)  # 核心接口 < 500ms
```

## 不同场景的断言策略

### 创建接口（POST）
```python
self.assert_status(response, 201)
self.assert_json_field(response, "$.data.id", exists=True)
# 数据库验证记录已创建
self.assert_db_record("SELECT ...", params=[...], exists=True)
```

### 查询接口（GET）
```python
self.assert_status(response, 200)
self.assert_json_field(response, "$.data", exists=True)
# 分页场景
self.assert_json_field(response, "$.data.total", exists=True)
self.assert_json_length(response, "$.data.list", min_length=1)
```

### 更新接口（PUT/PATCH）
```python
self.assert_status(response, 200)
# 验证返回的数据已更新
self.assert_json_field(response, "$.data.name", expected="新名称")
# 数据库验证已更新
self.assert_db_field("SELECT ...", params=[...], field="name", expected="新名称")
```

### 删除接口（DELETE）
```python
self.assert_status(response, 200)  # 或 204
# 数据库验证记录已删除（逻辑删除）
self.assert_db_field("SELECT ...", params=[...], field="is_deleted", expected=1)
# 或物理删除
self.assert_db_record("SELECT ...", params=[...], exists=False)
```

### 异常接口
```python
# 参数缺失
self.assert_status(response, 400)
self.assert_json_field(response, "$.message", exists=True)

# 未授权
self.assert_status(response, 401)

# 资源不存在
self.assert_status(response, 404)
self.assert_json_field(response, "$.message", exists=True)
```

## 禁止事项

- ❌ 不要使用 `assert response.status_code == 200`（使用 `self.assert_status`）
- ❌ 不要使用 `assert response.json()["data"]["id"]`（使用 `self.assert_json_field`）
- ❌ 不要忘记状态码断言（每个请求必须有）
- ❌ 不要只断言状态码（至少断言一个响应体字段）
