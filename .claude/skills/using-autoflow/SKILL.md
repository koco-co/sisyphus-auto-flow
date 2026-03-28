---
name: using-autoflow
description: 了解 sisyphus-auto-flow 的项目工作流、环境准备、release 选择，以及下一步该做什么
triggers:
  - using-autoflow
  - autoflow
  - 工作流怎么用
  - 如何使用这个项目
  - 安装环境
---

# using-autoflow

## 这个技能做什么

这个技能用于向用户解释 `sisyphus-auto-flow` 的完整工作流，并引导下一步操作。

## 先做什么

1. 先提醒用户阅读 `Install.md`
2. 说明默认 release 是 `release_6.2.x`
3. 说明小 HAR 与大 HAR / 多场景 HAR 的处理差异
4. 告诉用户可直接提供 HAR 文件，或先执行源码同步

## 关键命令

```bash
.claude/scripts/sync_release_repos.sh release_6.2.x
.claude/scripts/parse_har.sh path/to/file.har .data/parsed/parsed_requests.json
.claude/scripts/plan_har_workflow.sh .data/parsed/parsed_requests.json release_6.2.x .data/parsed/file.workflow.json
.claude/scripts/render_acceptance_summary.sh .data/parsed/file.workflow.json
```

`parse_har.sh` 会保留用户原始 HAR，并在 `.data/har/` 中使用工作区副本完成解析与回收站清理。

## 工作流说明

1. 先按 `Install.md` 把本地环境准备好
2. 选择 release，默认 `release_6.2.x`
3. 用 `.claude/scripts/sync_release_repos.sh` 同步后端源码
4. 解析 HAR，再基于 `parsed.json` 生成 workflow manifest
5. 若为大 HAR / 多场景 HAR，则由 `.claude/agents/` 中的多 agent 合同按模块 / 资源域协同处理
6. 仅执行当前 HAR 影响到的测试范围
7. 在终端输出验收清单，不额外生成跟踪文件

## 下一步如何引导用户

- 如果用户还没装环境：引导他先完成 `Install.md`
- 如果用户已准备好 HAR：让他直接给出 HAR 文件
- 如果用户要查源码：提醒先同步对应 release 的 `.repos/`
