# 代码提交规范

## 提交格式（Conventional Commits）

```
<type>(<scope>): <简短描述>

<详细说明（可选）>

<footer>
```

## Type 枚举

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新增功能/测试用例 | `feat(assets): 新增数据地图 CRUD 测试` |
| `fix` | 修复 bug/断言错误 | `fix(assets): 修复数据地图查询断言字段路径` |
| `data` | 测试数据变更 | `data(assets): 更新 MySQL 数据源测试数据` |
| `refactor` | 重构（不改变行为） | `refactor(core): 提取公共断言方法` |
| `docs` | 文档变更 | `docs: 更新 README 项目结构` |
| `style` | 代码格式 | `style: ruff format 格式化` |
| `test` | 框架测试（非业务） | `test(core): 补充 BaseAPITest 单元测试` |
| `chore` | 构建/工具 | `chore: 更新 pyproject.toml 依赖` |
| `ci` | CI/CD | `ci: 添加 GitHub Actions 工作流` |

## Scope 枚举

Scope 与业务模块/框架模块一一对应：

| Scope | 含义 |
|-------|------|
| `assets` | 数据资产 |
| `batch` | 离线开发 |
| `stream` | 实时开发 |
| `datasource` | 数据源管理 |
| `tag` | 标签引擎 |
| `easyindex` | 指标管理 |
| `dataapi` | 数据 API |
| `core` | 框架核心（base, assertions, extractors, models） |
| `fixtures` | pytest fixtures |
| `plugins` | pytest 插件 |
| `config` | 配置文件 |
| `registry` | 模块注册表 |
| 无 scope | 全局/跨模块变更 |

## 原子化规则

### 1. 一个提交 = 一个逻辑变更

- ✅ `feat(assets): 新增数据地图创建接口测试`
- ❌ `feat: 新增数据地图和数据源所有测试`（粒度太大）

### 2. 测试代码与测试数据分开提交

```
# 先提交数据
data(assets): 新增数据地图 CRUD 测试数据

# 再提交用例
feat(assets): 新增数据地图 CRUD 测试用例
```

### 3. 框架变更与业务变更分开提交

```
# 先提交框架
refactor(core): 新增 assert_json_batch 批量断言方法

# 再提交业务
feat(assets): 使用批量断言优化数据地图测试
```

### 4. 配置变更独立提交

```
chore(config): 新增 staging 环境数据源配置
```

### 5. API 端点注册独立提交

```
feat(assets): 注册数据地图相关 API 端点
```

## AI 辅助提交模板

Agent 生成提交时必须遵循以下格式：

```
{type}({scope}): {动作}{对象}{补充}

- {变更说明 1}
- {变更说明 2}

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

### 完整示例

```
feat(assets): 新增数据地图 CRUD 闭环测试

- 覆盖 MySQL/Hive 两种数据源类型
- 包含创建、查询、更新、删除完整流程
- 测试数据参数化，支持扩展更多数据源

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

```
data(assets): 新增数据地图 CRUD 测试数据

- 新增 testdata/assets/data_map_crud_data.py
- 包含 MySQL/Hive 正向数据 + 异常场景数据

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

```
refactor(core): 重命名 harness→core, validators→assertions

- harness/ 重命名为 core/（更准确表达框架核心语义）
- validators/ 重命名为 assertions/（避免与 pydantic 概念混淆）
- 全量更新导入路径
- 保留旧路径兼容 shim（DeprecationWarning）

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

## 禁止事项

- ❌ 不要在一个提交中混合框架代码和业务测试代码
- ❌ 不要在一个提交中修改多个不相关的业务模块
- ❌ 不要提交无意义的 message（如 `update`, `fix`, `wip`）
- ❌ 不要忘记 Co-authored-by trailer（AI 辅助标识）
- ❌ 不要提交包含敏感信息的代码（密码、token）
