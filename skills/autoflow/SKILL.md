---
name: autoflow
description: "从 HAR 文件生成 pytest 测试套件，结合源码进行 AI 智能分析。触发方式：/autoflow <har-path>、'从 HAR 生成测试'、提供 .har 文件路径。"
argument-hint: "<har-file-path> [--quick] [--resume]"
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, AskUserQuestion
---

# AutoFlow：HAR 转 Pytest 测试生成技能

将浏览器 HAR 抓包文件转换为完整的 pytest 测试套件，
采用四波次编排流水线：解析、分析、生成、评审。

---

## 预检阶段

解析 `$ARGUMENTS`，提取以下参数：
- `har_path` — 第一个位置参数（必填）
- `--quick` — 跳过第二波次的用户确认
- `--resume` — 从上次保存的检查点恢复

**1. 环境检查**

```bash
test -f repo-profiles.yaml || echo "MISSING"
```

若 `repo-profiles.yaml` 不存在：

```
AutoFlow 需要已初始化的项目。
请先运行 /using-autoflow，再重试。
```

立即终止。

**2. 恢复检查**

```bash
test -f .autoflow/state.json && cat .autoflow/state.json
```

若 `state.json` 存在且未设置 `--resume`：

```
AskUserQuestion(
  "发现中断的会话（波次 <N>，HAR：<har>）。\n"
  "请选择处理方式：\n"
  "A) 从波次 <N> 继续\n"
  "B) 重新开始\n"
  "C) 仅查看会话摘要"
)
```

处理完各选项后再继续。

**3. HAR 校验**

```bash
python3 -c "
import json, sys
data = json.load(open('${har_path}'))
assert 'log' in data and 'entries' in data['log'], '无效的 HAR 文件'
print(f'entries: {len(data[\"log\"][\"entries\"])}')
"
```

若校验失败，打印明确的错误信息并终止。

**4. 参数摘要**

打印已确认的输入信息：

```
HAR 文件：  <path>  （<N> 条记录）
模式：      quick=<是/否>  resume=<是/否>
```

---

## 第一波次：解析与准备（并行）

初始化会话状态文件：

```bash
python3 scripts/state_manager.py init --har "${har_path}"
```

**并行**启动两个 Agent（单条消息，两次 Agent 调用）：

```
Agent(
  name="har-parser",
  description="将 HAR 文件解析为结构化的请求/响应数据",
  model="claude-haiku-4-5",
  prompt="
    读取 HAR 文件：${har_path}
    同时读取：prompts/har-parse-rules.md
    将所有条目解析写入 .autoflow/parsed.json：
      - method、url、status、请求头/请求体、响应体
      - 按服务分组（使用 repo-profiles.yaml 中的 url_prefixes 进行映射）
    写入 .autoflow/parsed.json 后退出。
  "
)

Agent(
  name="repo-syncer",
  description="同步源码仓库并构建代码索引",
  model="claude-haiku-4-5",
  prompt="
    读取 repo-profiles.yaml。
    对列表中的每个仓库：
      - 运行：git -C <local_path> pull --ff-only
      - 收集：模块名、类名、路由装饰器
    写入 .autoflow/repo-status.json：
      { repo: string, branch: string, synced: bool, modules: string[] }
    完成后退出。
  "
)
```

等待两个 Agent 均完成。读取 `.autoflow/parsed.json` 和
`.autoflow/repo-status.json`，验证输出正确后再继续。

检查点：

```bash
python3 scripts/state_manager.py advance_wave --wave 1
```

---

## 第二波次：场景分析（顺序执行，交互式）

启动场景分析器（`--quick` 模式下跳过）：

```
Agent(
  name="scenario-analyzer",
  description="对照源码分析 HAR 流量，生成测试场景",
  model="claude-opus-4-5",
  prompt="
    读取：.autoflow/parsed.json
    读取：repo-profiles.yaml（用于定位源码仓库）
    从 .repos/ 读取相关源码文件，理解业务逻辑。
    读取：prompts/scenario-enrich.md
    读取：prompts/assertion-layers.md

    生成 .autoflow/scenarios.json：
    {
      services: [
        {
          name: string,
          repo: string,
          endpoints: [
            {
              method, path, source_file, source_fn,
              scenarios: [
                { id, name, type, priority, assertions: AssertionLevel[] }
              ]
            }
          ]
        }
      ],
      generation_plan: [
        { module: string, file: string, endpoint_ids: string[] }
      ]
    }

    AssertionLevel：L1=状态码, L2=Schema, L3=业务逻辑, L4=数据库, L5=副作用
  "
)
```

读取 `.autoflow/scenarios.json`。若设置了 `--quick`，直接跳到检查点。

否则展示确认清单：

```
AskUserQuestion(
  "=== 第二波次：场景分析完成 ===\n\n"
  "源码仓库：    <列表及分支名>\n"
  "HAR 覆盖率：  <N> 个服务，<M> 个接口\n\n"
  "AI 推断场景：\n"
  "  正常路径：  <N> 个\n"
  "  异常用例：  <N> 个\n"
  "  边界用例：  <N> 个\n\n"
  "AI 补充场景（增删改查 / 边界值）：\n"
  "  新增：      <N> 个\n\n"
  "断言层级：\n"
  "  L1（状态码）：  所有接口\n"
  "  L2（Schema）：  <N> 个接口\n"
  "  L3（业务逻辑）：<N> 个接口\n"
  "  L4（数据库）：  <N> 个接口（需配置数据库）\n"
  "  L5（副作用）：  <N> 个接口\n\n"
  "输出文件：\n"
  "  <generation_plan 中的文件列表>\n\n"
  "确认并继续？（yes / modify / cancel）"
)
```

若用户需要修改：询问具体变更内容，更新 `scenarios.json`，
并重新展示确认清单。

检查点：

```bash
python3 scripts/state_manager.py advance_wave --wave 2
```

---

## 第三波次：代码生成（并行扇出）

读取 `.autoflow/scenarios.json` → `generation_plan` 数组。

对计划中的每个模块，并行启动一个 Agent：

```
Agent(
  name="case-writer",
  description="为分配的接口生成 pytest 测试模块",
  model="claude-sonnet-4-5",
  prompt="
    你负责的模块：<module_name>
    分配的接口：<endpoint_ids>

    读取：
      - .autoflow/scenarios.json  （获取场景详情）
      - .autoflow/parsed.json     （获取真实的请求/响应示例）
      - prompts/code-style-python.md
      - prompts/assertion-layers.md
      - scenarios.json 中各接口对应的源码文件

    写入：tests/<module_name>.py
      - 每个场景对应一个测试函数
      - 基于 Fixture 的认证与客户端初始化
      - 按 scenarios.json 中指定的层级编写断言
      - 添加类型注解和文档字符串，不硬编码凭证
  "
)
```

所有代码生成器并行运行（单条消息，每个模块一次 Agent 调用）。
等待全部完成。

检查点：

```bash
python3 scripts/state_manager.py advance_wave --wave 3
```

---

## 第四波次：评审 + 执行 + 交付（顺序执行，交互式）

**评审**

```
Agent(
  name="case-reviewer",
  description="评审所有生成的测试文件，检查质量与正确性",
  model="claude-opus-4-5",
  prompt="
    读取所有匹配 tests/test_*.py 的文件
    读取：prompts/review-checklist.md
    读取：prompts/assertion-layers.md

    生成 .autoflow/review-report.json：
    {
      files_reviewed: number,
      issues: [{ file, line, severity, message, suggestion }],
      assertion_coverage: { L1: %, L2: %, L3: %, L4: %, L5: % },
      auto_fixes: [{ file, description }]
    }

    将可自动修复的问题直接应用到测试文件中。
  "
)
```

**执行**

```bash
python3 scripts/test_runner.py --output .autoflow/execution-report.json
```

**验收报告**

读取 `.autoflow/review-report.json` 和 `.autoflow/execution-report.json`。

```
AskUserQuestion(
  "=== 第四波次：验收报告 ===\n\n"
  "生成结果：\n"
  "  测试文件：    <N> 个\n"
  "  测试函数：    <N> 个\n"
  "  评审问题：    <critical> 个严重，<high> 个高危，<low> 个低危\n\n"
  "断言覆盖率：\n"
  "  L1（状态码）：         <N>%\n"
  "  L2（Schema）：         <N>%\n"
  "  L3（业务逻辑）：       <N>%\n"
  "  L4（数据库）：         <N>%\n"
  "  L5（副作用）：         <N>%\n\n"
  "执行结果：\n"
  "  通过：<N>  失败：<N>  跳过：<N>\n\n"
  "生成文件：\n"
  "  <tests/*.py 文件列表>\n\n"
  "验收命令：\n"
  "  make test-all   — 运行完整测试套件\n"
  "  make report     — 打开 HTML 报告\n\n"
  "确认并归档？（yes / review-failures / cancel）"
)
```

**通知与归档**

若 `.env` 中配置了 Webhook：

```bash
python3 scripts/notifier.py \
  --report .autoflow/execution-report.json \
  --review .autoflow/review-report.json
```

归档本次会话：

```bash
python3 scripts/state_manager.py archive
```

打印最终摘要：

```
AutoFlow 完成
─────────────────────────────────────────────
已生成测试：  <N> 个函数，分布在 <M> 个文件中
通过：        <N>  失败：<N>  跳过：<N>
会话已归档：  .autoflow/archive/<timestamp>/
─────────────────────────────────────────────
运行：make test-all
```
