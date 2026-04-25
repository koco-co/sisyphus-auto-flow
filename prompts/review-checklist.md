# 用例审查清单

> 引用方：`agents/case-reviewer.md`
> 用途：`case-reviewer` Agent 的审查标准和自动修正阈值。

---

## 使用说明

1. 阅读每个生成测试文件，对每项检查记录 `通过`/`失败`/`不适用`
2. 统计失败总数并计算偏差率
3. 根据阈值执行对应的修正动作，输出 `.tide/review-report.json`

---

## 1. 断言完整性

```
              L1      L2      L3      L4      L5
interface/    必须    必须    必须    可选    可选
scenariotest/ 必须    必须    必须    必须    必须
unittest/     —       —       必须    必须    可选
```

- **L1**: 已调用 `assert_protocol()`，`expected_status` 与 HAR 一致，`max_time_ms` 为 `max(har_time_ms * 3, 1000)`
- **L2**: Pydantic `BaseModel` 已定义，使用 `model_validate()`，嵌套对象已建模
- **L3**: 枚举校验、业务码检查（命名常量）、范围检查、分页不变量
- **L4**: CRUD 步骤验证数据、状态转换、DB 断言有 `if db:` 守卫
- **L5**: 来源注释 `# L5[置信度]: 源文件:行号 — 推断依据`，SPECULATIVE 不出现在 interface/

---

## 2. 场景完整性 & 代码质量

- CRUD 测试：4 种操作 + 验证步骤 + yield fixture 清理
- 异常路径：资源不存在、权限拒绝场景已覆盖
- 边界值：零值/负值/最大值/约束边界值
- 参数校验：缺少必填字段、空字符串测试
- 无内联魔法数字、无 fixture 修改、API fixture 使用 yield
- 文件 < 400 行、测试方法 < 50 行、嵌套深度 <= 4 层、所有函数有类型注解

---

## 3. 可运行性检查

- 所有符号已导入（无 NameError），`client`/`db` fixture 可用
- `pytest --collect-only` 通过（无 SyntaxError/ImportError/FixtureLookupError）

---

## 4. 偏差阈值与修正动作

```
偏差率 = 失败项数量 / 适用检查总数 * 100%
```

| 偏差率 | 处理动作 |
|--------|---------|
| < 15% | 静默修复 |
| 15–40% | 修复并标记（添加 flag_items） |
| > 40% | 阻塞并升级，请求指导 |

AskUserQuestion 使用场景：偏差率 > 40%、L4/L5 解读歧义、缺少源码、2 次修复后仍无法运行。

---

## 5. 审查报告输出

写入 `.tide/review-report.json`：

```json
{
  "reviewed_at": "<ISO8601>",
  "files_reviewed": ["..."],
  "total_checks": 42, "passed": 38, "failed": 4,
  "deviation_rate": 9.5,
  "action_taken": "silent_fix",
  "issues_found": [
    {
      "file": "tests/interface/...",
      "check": "L1 协议断言",
      "line": 45,
      "severity": "MEDIUM",
      "description": "max_time_ms 硬编码...",
      "fixed": true
    }
  ]
}
```

严重程度：CRITICAL（断言缺失）、HIGH（逻辑错误）、MEDIUM（不够优化）、LOW（风格问题）。
