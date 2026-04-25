# 场景丰富策略

> 引用方：`agents/scenario-analyzer.md`
> 用途：`scenario-analyzer` Agent 的规则，用于从 HAR 接口 + 源码分析中生成全面的测试场景。

---

## 1. 源码分析策略

对 `parsed.json` 中的每个接口，按 `Controller → Service → DAO/Mapper` 逐层追踪源码。

1. **定位 Controller**：搜索与接口路径匹配的路由注解（`@PostMapping`、`@GetMapping` 等）
2. **追踪 Service**：提取业务逻辑分支、权限检查、校验逻辑、外部调用、异常抛出、状态转换
3. **追踪 DAO**：提取表名、SQL 条件、字段约束、关联 JOIN
4. **识别关联接口**：扫描同一 Controller 中的其他 `@XxxMapping` 方法，检测 CRUD 闭环组

---

## 2. 八种场景类别

| # | 类别 | 优先级 | 适用条件 | 断言层 |
|---|------|--------|---------|--------|
| 1 | HAR 直接场景 | HIGH | HAR 中 status=200 且响应体非空的接口 | L1+L2+L3 |
| 2 | CRUD 闭环场景 | HIGH | Controller 中有完整 CRUD 方法组 | L1+L2+L3+L4+L5 |
| 3 | 参数校验场景 | MEDIUM | `@Valid`、`@NotNull`、`@NotBlank` 注解 | L1+L2 |
| 4 | 边界值场景 | MEDIUM | `@Min/@Max`、`@Size`、分页参数 | L1+L2+L3 |
| 5 | 权限校验场景 | HIGH* | `@PreAuthorize`、角色检查、手动权限校验 | L1+L2+L5 |
| 6 | 状态机场景 | HIGH* | 状态枚举 + 转换守卫 | L1+L2+L3+L4 |
| 7 | 关联数据联动场景 | MEDIUM | 跨服务调用、外键 JOIN、`@Transactional` | L1+L2+L4 |
| 8 | 异常路径场景 | HIGH | 每个接口最少：资源不存在、重复创建、无效引用 | L1+L2 |

*仅当源码中有明确信号时。

---

## 输出校验规则

1. endpoint_ids 非空
2. ID 引用有效（可在 `services[].endpoints[].id` 中找到）
3. 完全覆盖（每个 endpoint 至少分配给一个 worker）
4. HAR 场景完整（每个 endpoint 至少有一个 `har_direct` 基础场景）
