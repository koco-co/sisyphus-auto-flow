# sisyphus-auto-flow

> AI 驱动的接口自动化测试用例生成工作流

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://docs.astral.sh/ruff/)

## 简介

`sisyphus-auto-flow` 是一个基于 Coding Agent（Claude Code、Codex、Copilot）的接口自动化测试用例生成工作流。
它能将浏览器录制的 HAR 文件自动转化为标准化的 pytest 测试用例，并结合源码分析，智能补全测试场景。

### 核心特性

- 🎯 **HAR 驱动** — 从真实的浏览器操作录制中提取接口信息
- 🤖 **AI 辅助** — Coding Agent 自动分析源码，补全 CRUD 闭环
- 📐 **Harness 工程** — 标准化的测试基类、断言方法、代码风格
- 🔄 **自动修复** — 测试失败后自动分析、修复、重跑
- 📊 **Allure 报告** — 生成可视化的测试报告

### 工作流程

```
HAR 文件 → 解析提取 → 源码分析 → 场景确认 → 代码生成 → 自动执行 → 报告验收
```

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/koco-co/sisyphus-auto-flow.git
cd sisyphus-auto-flow

# 安装依赖
make install

# 运行测试
make test
```

## 技术栈

| 组件 | 技术选型 |
|------|---------|
| 运行环境 | Python 3.13+ |
| 包管理 | uv |
| 测试框架 | pytest 8.x |
| HTTP 客户端 | httpx |
| 数据校验 | pydantic 2.x |
| 类型检查 | pyright |
| 代码规范 | ruff + pre-commit |
| 测试报告 | allure-pytest |
| 日志 | loguru |
| 模板引擎 | jinja2 |

## 开发命令

```bash
make install         # 安装依赖 + Git hooks
make lint            # 代码检查
make format          # 代码格式化
make type-check      # 类型检查
make test            # 运行所有测试
make test-smoke      # 运行冒烟测试
make test-report     # 生成 Allure 报告
make clean           # 清理构建产物
```

## 项目结构

```
src/sisyphus_auto_flow/
├── harness/          # Harness 工程核心
│   ├── base_test.py  # 测试基类
│   ├── fixtures/     # pytest fixtures
│   ├── models/       # Pydantic 数据模型
│   ├── validators/   # 断言工具库
│   ├── extractors/   # 变量提取器
│   └── utils/        # 工具集
├── scripts/          # 工具脚本
└── generator/        # 代码生成引擎

tests/                # 测试用例
config/               # 多环境配置
```

## License

MIT
