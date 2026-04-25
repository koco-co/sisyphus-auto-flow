# 断言层（Assertion Layers）L1-L5

> 引用方：`agents/scenario-analyzer.md`、`agents/case-writer.md`
> 用途：每个断言层的生成规则。在每个测试中按 L1 → L2 → L3 → L4 → L5 的顺序应用。

---

## 断言层与测试类型矩阵

```
              L1      L2      L3      L4      L5
interface/    必须    必须    必须    可选    可选
scenariotest/ 必须    必须    必须    必须    必须
unittest/     —       —       必须    必须    可选
```

图示：`必须` = 始终生成，`可选` = 源码信号充分时生成，`—` = 不适用

---

## L1 — 协议层

验证 HTTP 层面正确性：状态码、响应时间、Content-Type。生成来源：HAR 响应元数据。

| 断言 | 来源 | 公式 |
|------|------|------|
| `status_code` | HAR `response.status` | 使用 HAR 精确值 |
| `max_time_ms` | HAR `response.time_ms` | `max(har_time_ms * 3, 1000)` — 最小 1000ms |
| `content_type` | 响应 Content-Type 请求头 | 使用 HAR 精确值 |

错误场景测试将 `expected_status` 设为对应错误码。期望 HTTP 200 返回业务错误的场景仍断言 `expected_status=200`，L3 检查业务码。

## L2 — 结构层

验证 JSON 响应体结构：字段存在性、类型、必填与可选。生成来源：HAR 响应体 + 源码 DTO/VO。

规则：创建 Pydantic `BaseModel`，使用 `model_validate(resp.json())`。嵌套对象必须有命名模型，同类型列表用 `list[SubModel]`。源码 `@NotNull` 对应必填字段，无注解对应可选。

## L3 — 数据层

验证值的正确性：枚举值、数值范围、业务码、格式、分页不变量。生成来源：源码枚举/常量、`@Min/@Max` 注解、字段命名约定、分页参数。

业务成功码使用模块级常量。格式字段从命名推断（phone/email/createTime 等）。分页检查：`totalCount >= 0`、列表长度不超过 `pageSize`。

## L4 — 业务层

验证业务规则一致性、状态机正确性、CRUD 数据完整性、DB 状态。生成来源：源码业务逻辑、状态枚举、Service 层条件分支、DAO SQL。

CRUD 测试中每次写操作后通过 API 验证变更。DB 断言仅对写操作生成，包裹在 `if db:` 守卫中。DB 只读操作：`query_one`、`query_all`、`count`（无 execute/insert）。

## L5 — AI 推断层

验证隐式规则：安全边界、隐藏限制、未文档化依赖、隐式状态约束。生成来源：深度源码分析。

每条 L5 断言必须包含注释：源文件路径+行号、推断依据、置信度（HIGH/SPECULATIVE）。interface/ 测试中只允许 HIGH 置信度。

---

## 汇总表

| 层级 | 输入 | 输出 |
|------|------|------|
| L1 | HAR `response.status`、`time_ms`、Content-Type | `assert_protocol(response, ...)` |
| L2 | HAR 响应体 JSON + 源码 DTO/VO | Pydantic `BaseModel` + `model_validate()` |
| L3 | 源码枚举、`@Min/@Max`、字段名、分页 | `assert value in (...)`、范围检查、格式正则 |
| L4 | 源码业务逻辑、状态机、DAO SQL | 多步 API 断言，可选 `if db:` DB 检查 |
| L5 | 深度源码阅读、方法名、注释 | 含 `来源:行号` + 置信度注释的断言 |
