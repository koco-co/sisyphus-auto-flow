# sisyphus-auto-flow

> AI 驱动的接口自动化测试用例生成工作流。将浏览器录制的 HAR 文件自动转化为标准化的 pytest 测试用例。

## 项目结构

```
sisyphus-auto-flow/
├── CLAUDE.md                         # ← 你正在读的文件（Agent 入口指令）
├── src/sisyphus_auto_flow/
│   ├── harness/                      # Harness 工程核心
│   │   ├── base_test.py              # 测试基类 — 所有测试必须继承
│   │   ├── conftest.py               # 全局 pytest fixtures
│   │   ├── fixtures/                 # 可复用 fixtures（认证/数据库/清理）
│   │   ├── models/                   # Pydantic 数据模型
│   │   ├── validators/               # 断言工具库
│   │   ├── extractors/               # 变量提取器（JSONPath/正则/Header）
│   │   ├── plugins/                  # pytest 插件
│   │   └── utils/                    # 工具（变量池/加密/日志）
│   ├── scripts/                      # 工具脚本（HAR 解析器等）
│   └── generator/                    # 代码生成引擎
├── tests/                            # 生成的测试用例（按业务模块组织）
├── config/                           # 多环境 YAML 配置
├── har_files/                        # HAR 文件输入目录
├── .repos/                           # 被测服务源码（仅供参考）
├── .trash/                           # 回收站（7天自动清理）
└── .claude/                          # Agent 配置（规则/技能/命令）
    ├── rules/                        # 代码规范文件
    ├── skills/har-to-testcase/       # HAR → 测试用例技能
    └── settings.json                 # 项目级 Agent 设置
```

## 工作流：HAR → 测试用例

当用户提供 HAR 文件时，**严格按以下 6 个步骤执行**：

### Step 1: 解析 HAR 文件
```bash
python -m sisyphus_auto_flow.scripts.parse_har <har_file> --output tmp/parsed_requests.json
```
解析完成后，自动将 HAR 文件移入 `.trash/` 回收站。

### Step 2: 阅读源码
浏览 `.repos/` 目录下的被测服务源码：
- 找到对应的接口处理器（Controller/Handler）
- 理解请求/响应模型、数据库模型
- 识别核心业务逻辑和校验规则

### Step 3: 交互式场景确认
向用户展示分析结果并等待确认：
1. **从 HAR 识别到的接口**列表
2. **建议补充的接口**（完善 CRUD 闭环、异常场景、边界场景）
3. **断言方案**（HTTP 状态码、JSON 字段、数据库记录、响应时间）
4. **数据库断言**（pre_sql 清理、post_sql 验证）

使用 Rich 面板格式化展示，确保可读性。用户确认后再继续。

### Step 4: 生成测试代码
- 所有测试**必须继承** `BaseAPITest` 基类
- 必须遵循 `.claude/rules/` 下的所有规范文件
- 使用 `.claude/skills/har-to-testcase/references/` 中的模板作为参考

### Step 5: 自动执行与修复
```bash
uv run pytest tests/<module>/ -v --alluredir=allure-results
```
如果测试失败：分析失败原因 → 自动修复 → 重新运行。循环直到全部通过。

### Step 6: 通知用户验收
生成 Allure 报告，通知用户查看测试结果。

## 代码生成规范（必读）

**在生成任何测试代码之前，必须先阅读以下规范文件：**

| 文件 | 内容 |
|------|------|
| `.claude/rules/CONVENTIONS.md` | 命名规范、文件结构、代码风格 |
| `.claude/rules/ASSERTIONS.md` | 断言优先级、使用规范 |
| `.claude/rules/PATTERNS.md` | 场景模式（CRUD/认证/异常/分页） |
| `.claude/rules/DATABASE.md` | 数据库断言模式 |
| `.claude/rules/EXAMPLES.md` | 完整的参考示例 |

## 核心约定速查

### 命名规范
- 测试文件：`test_{模块}_{场景}.py`（如 `test_user_crud.py`）
- 测试类：`Test{模块}{场景}`（如 `TestUserCRUD`）
- 测试方法：`test_{序号}_{动作}_{条件}_{预期}`（如 `test_01_create_user_with_valid_data_returns_201`）

### 用例结构
```python
"""用户管理 — CRUD 闭环测试。"""

import allure
import pytest

from sisyphus_auto_flow.harness.base_test import BaseAPITest


@allure.epic("用户管理")
@allure.feature("用户 CRUD")
class TestUserCRUD(BaseAPITest):
    """用户增删改查闭环测试。"""

    @allure.story("创建用户")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_01_create_user_with_valid_data_returns_201(self):
        """正向：使用有效数据创建用户，期望返回 201。"""
        # Arrange — 准备测试数据
        payload = {"name": f"test_user_{self.unique_id}", "email": f"{self.unique_id}@test.com"}

        # Act — 执行请求
        response = self.request("POST", "/api/v1/users", json=payload)

        # Assert — 验证结果
        self.assert_status(response, 201)
        self.assert_json_field(response, "$.data.id", exists=True)
        self.assert_json_field(response, "$.data.name", expected=payload["name"])

        # 提取变量供后续步骤使用
        user_id = self.extract_json(response, "$.data.id")
        self.save("user_id", user_id)
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
