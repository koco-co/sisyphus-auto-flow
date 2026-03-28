# sisyphus-auto-flow

> AI 驱动的接口自动化测试用例生成工作流

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://docs.astral.sh/ruff/)

## 简介

`sisyphus-auto-flow` 用于把浏览器录制的 HAR 文件转换成标准化 pytest 接口自动化测试，并结合源码分析、规则模板和 AI 工作流补全场景。

## AI 安装提示

按照 https://github.com/koco-co/sisyphus-auto-flow/blob/main/Install.md把它的本地开发环境初始化好

## 核心能力

- HAR 解析与归一化
- 小 HAR 轻量单 agent 流程
- 大 HAR / 多场景 HAR 自适应多 agent 流程
- 固定 release 选择与后端源码同步
- GitLab nested 仓库映射与 release 分支模板支持
- 优先参考 `.repos/dt-insight-web/*` 与 `.repos/dt-insight-qa/dtstack-httprunner/*`
- 只跑当前 HAR 影响到的测试范围
- 固定终端验收清单输出（含验收通知 / 参考源码 / 验收命令）

## 自适应工作流

1. 先选择 release，默认 `release_6.2.x`
2. 使用 `.claude/scripts/sync_release_repos.sh` 同步后端源码
3. 使用 `.claude/scripts/parse_har.sh` 解析 HAR（外部 HAR 会先暂存到 `.data/har/`，保留原文件）
4. 使用 `.claude/scripts/plan_har_workflow.sh` 基于 `parsed.json` 生成 workflow manifest
5. 生成 manifest 时优先补出参考源码：`.repos/dt-insight-web/*` 后端仓库，以及 `.repos/dt-insight-qa/dtstack-httprunner/api/*`、`config/configs.py`、`config/env_config.py`
6. 大 HAR / 多场景 HAR 由 `.claude/agents/` 中的多 agent 合同按模块 / 资源域拆分协同处理
7. 使用 `.claude/scripts/render_acceptance_summary.sh` 在终端输出固定验收清单

## 关键脚本

```bash
.claude/scripts/sync_release_repos.sh release_6.2.x
.claude/scripts/parse_har.sh path/to/file.har .data/parsed/parsed_requests.json
.claude/scripts/plan_har_workflow.sh .data/parsed/parsed_requests.json release_6.2.x .data/parsed/file.workflow.json
.claude/scripts/generate_tests.sh path/to/scenario.json tests/<module>/
.claude/scripts/render_acceptance_summary.sh .data/parsed/file.workflow.json
uv run pytest tests/<module>/ -v --alluredir=allure-results
```

`parse_har.sh` 会把仓库外的 HAR 先复制到 `.data/har/` 再调用解析器，因此真正被移入 `.trash/` 的是工作区副本，不会直接移动调用者原始文件。

`render_acceptance_summary.sh` 会固定输出：验收通知、参考源码、HAR 给出场景、AI 补充场景、涉及模块 / 菜单 / 功能 / 代码位置、验收命令、定向执行用例、跳过项与后续跟进。

## 技能与 agent 合同

- `.claude/skills/using-autoflow/SKILL.md`
- `.claude/skills/har-to-testcase/SKILL.md`
- `.claude/agents/har-decomposer.md`
- `.claude/agents/scenario-planner.md`
- `.claude/agents/test-writer.md`
- `.claude/agents/test-reviewer.md`
- `.claude/agents/targeted-executor.md`

## 项目结构

```text
.claude/                        # skills / agents / scripts / rules
.data/parsed/                   # HAR 解析结果和 workflow manifest
.repos/                         # 后端源码参考目录（不含 CustomItem）
src/sisyphus_auto_flow/         # runtime SDK 与 CLI
api/ tests/ testdata/           # 自动化代码三层映射
config/                         # 环境配置与 repositories.yaml
Install.md                      # 安装与初始化说明
CHANGELOG.md                    # 变更记录
```

## 开发命令

```bash
make install
make type-check
make lint
make test
make sync-repos RELEASE=release_6.2.x
```

## 下一步

如果你是第一次使用，建议先看 `.claude/skills/using-autoflow/SKILL.md`，然后直接给出一个 HAR 文件让我驱动完整流程。
