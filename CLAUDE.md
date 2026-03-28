# sisyphus-auto-flow

> AI 驱动的接口自动化测试用例生成工作流。将浏览器录制的 HAR 文件自动转化为标准化的 pytest 测试用例。

## 项目结构

```
sisyphus-auto-flow/
│
│  ── 隐藏基础设施 ──────────────────────────────────
├── .claude/                          # Agent 配置（规则/技能/命令/脚本）
│   ├── rules/                        # 代码规范文件
│   ├── skills/har-to-testcase/       # HAR → 测试用例技能 + Jinja2 模板
│   ├── scripts/                      # 工具脚本（清理等）
│   ├── hooks/                        # Agent 会话钩子
│   ├── commands/                     # 自定义 slash 命令
│   └── settings.json                 # 项目级 Agent 设置
├── .data/                            # 数据暂存（HAR 输入 / 解析中间文件）
│   ├── har/                          # HAR 文件输入目录
│   └── parsed/                       # 解析后的中间 JSON
├── .repos/                           # 被测服务源码（仅供参考）
├── .trash/                           # 回收站（会话启动时 7 天自动清理）
│
│  ── 框架源码（Python 可安装包）────────────────────
├── src/sisyphus_auto_flow/
│   ├── core/                         # 框架核心（基类/断言/提取器/模型）
│   │   ├── base.py                   # 测试基类 — 所有测试必须继承
│   │   ├── assertions/               # 断言工具库
│   │   ├── extractors/               # 变量提取器（JSONPath/正则/Header）
│   │   └── models/                   # Pydantic 数据模型
│   ├── fixtures/                     # 可复用 fixtures（认证/数据库/清理）
│   ├── plugins/                      # pytest 插件
│   ├── utils/                        # 工具（变量池/加密/日志）
│   ├── parsers/                      # 解析器（HAR/源码分析）
│   ├── generator/                    # 代码生成引擎
│   └── registry/                     # 模块映射注册表
│
│  ── 业务自动化代码（日常工作区）────────────────────
├── api/                              # API 端点定义层（Enum 注册）
│   └── {module}/                     # 按业务模块组织
├── tests/                            # 测试用例（按业务模块组织）
│   └── {module}/                     # 与 api/ 和 testdata/ 平行对应
├── testdata/                         # 测试数据层（与 tests/ 平行映射）
│   └── {module}/                     # 参数化数据集
├── config/                           # 多环境 YAML 配置
│
│  ── 标准根文件 ────────────────────────────────────
├── CLAUDE.md                         # ← 你正在读的文件（Agent 入口指令）
├── Makefile
├── README.md
├── pyproject.toml
└── uv.lock
```

### 平行映射关系

每个业务模块在三层中保持 **同名同结构**：

```
业务模块: assets
  ├── api/assets/assets_api.py            → 端点定义（URL Enum）
  ├── tests/assets/test_assets_crud.py    → 测试逻辑
  └── testdata/assets/assets_crud_data.py → 测试数据
```

模块映射注册表: `src/sisyphus_auto_flow/registry/module_registry.py`

## 工作流：HAR → 测试用例

当用户提供 HAR 文件时，先走 **release 选择 + 后端源码同步**，然后再进入解析/生成流程。

### Step 0: 选择 release

- 固定支持：
  - `release_5.3.x`
  - `release_6.0.x`
  - `release_6.2.x`（默认）
  - `release_6.3.x`
  - `release_7.0.x`

### Step 0.5: 同步后端源码

```bash
.claude/scripts/sync_release_repos.sh <release>
```

- 只同步后端源码仓库
- 前端源码不作为接口自动化参考
- `.repos/CustomItem` 不纳入标准工作流

### Step 1: 解析 HAR 并生成 workflow manifest

```bash
.claude/scripts/parse_har.sh <har_file> .data/parsed/parsed_requests.json
.claude/scripts/plan_har_workflow.sh .data/parsed/parsed_requests.json <release> .data/parsed/<name>.workflow.json
```

如果输入 HAR 位于仓库外部，wrapper 会先将其暂存到 `.data/har/`，然后解析并把这份工作区副本移入 `.trash/` 回收站，避免直接移动用户原始文件。

### Step 2: 自适应选择工作流

- 小 HAR / 单场景 HAR：主 agent 直接继续
- 大 HAR / 多场景 HAR：主 agent 读取 `.data/parsed/<name>.workflow.json`，并参考 `.claude/agents/` 按模块 / 资源域进行任务解耦与分派

建议 agent 角色：

- `.claude/agents/har-decomposer.md`
- `.claude/agents/scenario-planner.md`
- `.claude/agents/test-writer.md`
- `.claude/agents/test-reviewer.md`
- `.claude/agents/targeted-executor.md`

### Step 3: 阅读源码
浏览 `.repos/` 目录下的被测服务源码：
- 找到对应的接口处理器（Controller/Handler）
- 理解请求/响应模型、数据库模型
- 识别核心业务逻辑和校验规则

### Step 4: 交互式场景确认
向用户展示分析结果并等待确认：
1. **从 HAR 识别到的接口**列表
2. **建议补充的接口**（完善 CRUD 闭环、异常场景、边界场景）
3. **断言方案**（HTTP 状态码、JSON 字段、数据库记录、响应时间）
4. **数据库断言**（pre_sql 清理、post_sql 验证）

使用 Rich 面板格式化展示，确保可读性。用户确认后再继续。

### Step 5: 生成测试代码
- 所有测试**必须继承** `BaseAPITest` 基类
- 必须遵循 `.claude/rules/` 下的所有规范文件
- Agent 侧优先通过 `.claude/scripts/generate_tests.sh <scenario_json> tests/{module}/` 调用生成器
- 使用 `.claude/skills/har-to-testcase/references/` 中的模板作为参考
- 测试数据文件放入 `testdata/{module}/`，与 `tests/{module}/` 平行
- API 端点注册到 `api/{module}/{module}_api.py`

### Step 6: 自动执行与修复
```bash
uv run pytest tests/<module>/ -v --alluredir=allure-results
```
如果测试失败：分析失败原因 → 自动修复 → 重新运行。循环直到全部通过。

注意：只运行 workflow manifest 对应的模块/文件，不要默认全量跑业务测试。

### Step 7: 通知用户验收

```bash
.claude/scripts/render_acceptance_summary.sh .data/parsed/<name>.workflow.json
```

在命令行中输出验收清单，包含：

- HAR 给出的场景
- AI 补充场景
- 涉及模块 / 菜单 / 功能
- 代码位置
- 定向执行用例
- 跳过项 / 不纳入范围

如需用户快速了解项目工作流，优先引导到 `.claude/skills/using-autoflow/SKILL.md`。

## 代码生成规范（必读）

**在生成任何测试代码之前，必须先阅读以下规范文件：**

| 文件 | 内容 |
|------|------|
| `.claude/rules/CONVENTIONS.md` | 命名规范、文件结构、代码风格 |
| `.claude/rules/ASSERTIONS.md` | 断言优先级、使用规范 |
| `.claude/rules/PATTERNS.md` | 场景模式（CRUD/认证/异常/分页） |
| `.claude/rules/DATABASE.md` | 数据库断言模式 |
| `.claude/rules/EXAMPLES.md` | 完整的参考示例 |
| `.claude/rules/COMMITS.md` | 原子化提交规范 |

## 核心约定速查

### 命名规范
- 测试文件：`test_{模块}_{场景}.py`（如 `test_assets_crud.py`）
- 数据文件：`{模块}_{场景}_data.py`（如 `assets_crud_data.py`）
- API 定义：`{模块}_api.py`（如 `assets_api.py`）
- 测试类：`Test{模块}{场景}`（如 `TestAssetsCRUD`）
- 测试方法：`test_{序号}_{动作}_{条件}_{预期}`（如 `test_01_create_user_with_valid_data_returns_201`）

### 用例结构
```python
"""数据资产 — CRUD 闭环测试。"""

import allure
import pytest

from sisyphus_auto_flow.core.base import BaseAPITest
from testdata.assets.assets_crud_data import create_datasource_data


@allure.epic("数据资产")
@allure.feature("数据源 CRUD")
class TestAssetsCRUD(BaseAPITest):
    """数据资产增删改查闭环测试。"""

    @allure.story("创建数据源")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("data", create_datasource_data, ids=lambda d: d["case"])
    def test_01_create_datasource_with_valid_data_returns_200(self, data):
        """正向：使用有效数据创建数据源。"""
        # Arrange
        payload = {"source_type": data["source_type"], "datasource_name": data["datasource_name"]}

        # Act
        response = self.request("POST", "/dassets/v1/dataDb/batchAddDb", json=payload)

        # Assert
        self.assert_status(response, data["expected_status"])
        self.assert_json_field(response, "$.data.id", exists=True)
        self.save("datasource_id", self.extract_json(response, "$.data.id"))
```

### 断言优先级
1. HTTP 状态码（必须，永远第一个）
2. 响应体结构（必填字段存在性）
3. 响应体值（具体字段值匹配）
4. 数据库状态（如适用）
5. 响应时间（如有 SLA 要求）

### 变量传递
```python
# 从响应提取值
user_id = self.extract_json(response, "$.data.id")
self.save("user_id", user_id)

# 在后续请求中使用
self.request("GET", f"/api/v1/users/{self.load('user_id')}")
```

## 技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| Python | 3.13+ | 运行环境 |
| uv | latest | 包管理 |
| pytest | 8.x | 测试框架 |
| httpx | 0.28+ | HTTP 客户端（同步+异步） |
| pydantic | 2.x | 数据校验 |
| pyright | latest | 类型检查 |
| ruff | latest | 代码规范 |
| allure-pytest | latest | 测试报告 |
| loguru | latest | 日志 |
| jsonpath-ng | latest | JSON 提取 |
| pymysql | latest | 数据库断言 |
| jinja2 | latest | 模板渲染 |

## 开发命令

```bash
make install         # 安装依赖 + pre-commit hooks
make lint            # 代码规范检查
make format          # 自动格式化
make type-check      # 类型检查（pyright）
make test            # 运行全部测试
make test-smoke      # 仅运行冒烟测试
make test-report     # 运行测试并生成 Allure 报告
make clean           # 清理构建产物
```
