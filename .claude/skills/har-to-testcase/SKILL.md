---
name: HAR 转测试用例
description: 将 Chrome HAR 文件转换为标准化 pytest API 测试用例，并根据 HAR 规模自动选择轻量或多-agent 工作流
triggers:
  - har
  - 测试用例
  - 接口测试
  - 自动化测试
  - 生成用例
---

# HAR → 测试用例生成 Skill

## 概述

本 Skill 实现从 Chrome HAR 文件到标准化 pytest API 测试用例的完整转换工作流。

在新工作流中：

- 默认 release 为 `release_6.2.x`
- 先同步后端源码，再分析 HAR
- 小 HAR 保持轻量流程
- 大 HAR / 多场景 HAR 会借助 `.claude/agents/` 中的多 agent 合同

如果用户还没有准备环境，先引导他查看 `Install.md` 或 `.claude/skills/using-autoflow/SKILL.md`。

## 工作流程

### 第一步：选择 release 并同步后端源码

```bash
.claude/scripts/sync_release_repos.sh release_6.2.x
```

- 固定支持 `release_5.3.x` / `release_6.0.x` / `release_6.2.x` / `release_6.3.x` / `release_7.0.x`
- 默认 `release_6.2.x`
- 不参考 `.repos/CustomItem`

### 第二步：解析 HAR 并生成 workflow manifest

```bash
.claude/scripts/parse_har.sh <har文件路径> .data/parsed/parsed_requests.json
.claude/scripts/plan_har_workflow.sh <har文件路径> release_6.2.x .data/parsed/file.workflow.json
```

- 自动过滤静态资源
- 识别请求链和模块归属
- workflow manifest 是后续多 agent 协同的唯一中间契约

### 第三步：按 HAR 规模选择工作流

- 小 HAR：主 agent 直接继续
- 大 HAR / 多场景 HAR：主 agent 参考 `.claude/agents/` 分配 `har-decomposer`、`scenario-planner`、`test-writer`、`test-reviewer`、`targeted-executor`

### 第四步：生成测试代码

- 优先通过 `.claude/scripts/generate_tests.sh <scenario_json> tests/<模块>/` 调用运行时生成器
- 必须遵守 `.claude/rules/CONVENTIONS.md`
- 必须遵守 `.claude/rules/ASSERTIONS.md`
- 必须遵守 `.claude/rules/PATTERNS.md`

### 第五步：仅执行当前 HAR 影响范围

```bash
uv run pytest tests/<模块>/ -v --alluredir=allure-results
```

- 只跑当前 HAR 影响到的模块/文件
- 如果失败，主 agent 结合 reviewer 反馈继续修复

### 第六步：终端验收清单

```bash
.claude/scripts/render_acceptance_summary.sh .data/parsed/file.workflow.json
```

- 输出 HAR 给出场景
- 输出 AI 补充场景
- 输出涉及模块 / 菜单 / 功能 / 代码位置
- 输出定向执行用例与跳过项

## 依赖的规则文件

- `.claude/rules/CONVENTIONS.md`
- `.claude/rules/ASSERTIONS.md`
- `.claude/rules/PATTERNS.md`
- `.claude/rules/DATABASE.md`
- `.claude/rules/EXAMPLES.md`

## 关键约束

1. 所有测试类继承 `BaseAPITest`
2. 所有注释和文档使用中文
3. 严格遵守 Arrange-Act-Assert 模式
4. 断言优先级：状态码 → 结构 → 值 → 数据库 → 性能
5. `.claude/agents/` 与 workflow manifest 必须保持一致
