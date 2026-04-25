# Tide 全面优化设计

**日期**: 2026-04-25
**状态**: 草案
**目标版本**: v1.4

---

## 概述

针对 tide 在企业级 API 自动化测试项目中的实际使用场景，从生成质量、运行成本、扩展能力三个维度进行优化。

本次阶段聚焦四大模块：Convention 检测升级、Prompt 按需加载、dtstack 风格适配、Skill 编排优化。

---

## 1. Convention 检测升级

### 现状

`convention_scanner.py` 已能检测 HTTP 客户端、断言风格、Allure 标注等基本维度，但在面对 dtstack-httprunner 这类复杂企业项目时存在盲区：

- 断言风格误检为 `attr`，实际是 `resp['code'] == 1` + `resp['success'] == True`
- HTTP 客户端误检为 `DataApiRequests`（子类），实际主类是 `BaseRequests`
- 未检测：测试文件命名规范（`_test.py`）、pytest markers、`ENV_CONF` 模式、`Logger` 模式、`setup_class` 惯例
- 检测维度未与生成侧（case-writer）打通

### 改动方案

在 `scripts/convention_scanner.py` 中新增 5 个检测维度，输出到 `convention-scout.json`（已有文件格式不变）：

| 维度 | 检测目标 | dtstack 的检测结果 |
|------|---------|-------------------|
| **api_pattern** | Enum/Class/Inline | Enum (`BatchApi`, `CommonApi` 等 11 模块) |
| **http_client** | 自定义类/httpx/requests | `BaseRequests`, 位于 `utils/common/BaseRequests.py`, 方法签名 `post(self, url, desc, **kwargs)` |
| **assertion** | `code_success` / `status_only` / `json_path` | `resp["code"] == 1` + `resp["success"] == True`, 含辅助方法 `assert_response_success()` |
| **test_style** | 文件后缀、fixture 模式、markers | 后缀 `_test.py`, 用 `setup_class`, markers: `smoke`, `kerberos` |
| **allure_detail** | attach 方式、feature/story 层级 | 请求时自动 attach, `@allure.feature("离线开发")` 惯例 |

#### 检测实现方式

```python
# 每个维度是一个独立函数，签名统一
def detect_api_pattern(root: Path) -> dict | None: ...
def detect_http_client(root: Path) -> dict | None: ...
def detect_assertion(root: Path) -> dict | None: ...
def detect_test_style(root: Path) -> dict | None: ...
def detect_allure_detail(root: Path) -> dict | None: ...

# 主流程：运行所有检测器，合并结果
DETECTORS = [
    detect_api_pattern,
    detect_http_client,
    detect_assertion,
    detect_test_style,
    detect_allure_detail,
    # 后续新增项目风格只需追加检测器
]
```

#### 设计原则

- **不破坏现有数据**：旧字段不动，只追加新检测块
- **检测失败降级**：检测不到的自定义模式返回 `null`，不阻断流程
- **统一 AST 工具函数**：公共的 enum/class/method/import 检测逻辑抽到 `_ast_utils`
- **输出格式一致**：所有检测器返回 `dict | None`

---

## 2. Prompt 按需加载

### 现状

执行 `/tide` 时，Agent 的 system prompt 会全量注入对应 prompt 文件（如 `code-style-python.md` 200+ 行），其中约 60% 的内容在当前场景下并不需要。

### 改动方案

将 `prompts/` 目录重组为"核心 + 条件模块"结构：

```
prompts/
├── code-style-python/
│   ├── _index.md              ← 加载清单定义（仅供 skill 读取）
│   ├── 00-core.md             ← 通用规范，所有项目都需要 (~60行)
│   ├── 10-api-enum.md         ← Enum 风格 API 规范 (~20行)
│   ├── 10-api-class.md        ← Class 风格 API 规范 (~20行)
│   ├── 10-api-inline.md       ← 内联 URL 规范 (~15行)
│   ├── 20-client-custom.md    ← 自定义客户端调用规范 (~25行)
│   ├── 20-client-httpx.md     ← httpx 客户端规范 (~15行)
│   ├── 20-client-requests.md  ← requests 客户端规范 (~15行)
│   ├── 30-assert-code-success.md  ← resp['code']==1 断言 (~15行)
│   ├── 30-assert-status-only.md   ← status_code 断言 (~10行)
│   ├── 40-test-structure-dtstack.md  ← _test.py + setup_class (~20行)
│   └── 40-test-structure-standard.md  ← conftest fixture 模式 (~15行)
├── assertion-layers/
│   └── 00-core.md             ← L1-L5 定义精简版 (~30行)
├── har-parse-rules.md         ← 保持不变
├── review-checklist.md        ← 精简，只留核心评审标准 (~40行)
└── scenario-enrich.md         ← 精简，只留核心场景策略 (~50行)
```

#### 加载规则

由 `tide/SKILL.md` 在读取 `convention-scout.json` + `convention-fingerprint.yaml` 后动态决定加载哪些模块：

```
# 伪代码：skill 中的按需组合逻辑
prompt_modules = ["00-core"]  # 始终加载

match fingerprint:
  api_pattern == "enum"      → + "10-api-enum"
  http_client == "custom"    → + "20-client-custom"
  assertion == "code_success" → + "30-assert-code-success"
  test_style.markers         → + "40-test-structure-dtstack"
  # ...
```

#### 效果预期

| 场景 | 优化前 | 优化后 | 节省 |
|------|--------|--------|------|
| dtstack-httprunner | ~250 行 prompt | ~130 行 | ~48% |
| 全新项目(httpx) | ~250 行 | ~120 行 | ~52% |
| 已有项目(requests) | ~250 行 | ~140 行 | ~44% |

#### 命名规范

- 前缀 `00-`：核心，始终加载
- 前缀 `10-` ~ `40-`：条件加载，按主题分组
- `_index.md`：仅供 skill 读取的映射表（可选）

---

## 3. dtstack 风格适配

### 现状

当前 case-writer 生成的是 httpx + pydantic 风格测试代码，与 dtstack-httprunner 的实际编码风格不匹配：

| 维度 | 当前默认输出 | dtstack 实际风格 |
|------|-------------|-----------------|
| API 路径 | `httpx.Client().post(url)` 字符串 | `BatchApi.create_project.value` Enum 导入 |
| HTTP 客户端 | `httpx.Client()` | `BaseRequests().post(url, desc)` |
| 断言 | `resp.status_code == 200` | `resp["code"] == 1, resp["message"]` |
| 测试结构 | `def test_xxx():` 独立函数 | `class TestXxx:` + `setup_class` |
| 测试文件 | `test_xxx.py` | `xxx_test.py` |
| Allure | 手动 attach | 自动 attach（BaseRequests 内置） |
| 日志 | 无 | `Logger('模块名')()` |
| 配置读取 | 全局变量 | `ENV_CONF.base_url` |
| pytest marker | 无 | `@pytest.mark.smoke` |

### 改动方案

**不改 Python 代码，通过 prompt 指令驱动生成风格变化。**

在 `prompts/code-style-python/` 各条件模块中定义 fingerprint → 代码风格的映射规则：

**`10-api-enum.md`（新增）：**
```markdown
当 fingerprint.api_pattern.type == "enum" 时：
- 从 fingerprint.api_pattern.modules 中找出对应模块的 Enum 类
- 使用 `{EnumClass}.{endpoint_name}.value` 获取 URL 路径
- 不再硬编码 URL 字符串
- 示例：
  ```python
  from api.batch.batch_api import BatchApi
  url = ENV_CONF.base_url + BatchApi.create_project.value
  ```
```

**`20-client-custom.md`（新增）：**
```markdown
当 fingerprint.http_client.type == "custom_class" 时：
- 从 fingerprint.http_client 读取类名和模块路径
- 在 `setup_class` 中实例化：`self.client = {ClassName}()`
- 调用方法签名匹配检测到的签名：`self.client.{method}(url, desc, **kwargs)`
- 不使用 httpx/requests 裸调用
```

**`30-assert-code-success.md`（新增）：**
```markdown
当 fingerprint.assertion.style == "code_success" 时：
- 主断言：`assert resp["code"] == 1, resp["message"]`
- 成功断言：`assert resp["success"] is True`
- 使用辅助方法（若检测到）：`self.client.assert_response_success()`
```

**`40-test-structure-dtstack.md`（新增）：**
```markdown
当 fingerprint.test_style.markers 存在时：
- 在类级别应用 markers：`@pytest.mark.{first_marker}`
- 测试类包含 `setup_class` 方法
- 测试文件以 `_test.py` 结尾
- 类 docstring 格式：`"""测试-{序号} {描述}"""`
```

### 新增 fixture 和 cleanup 生成（可选增强）

根据检测结果，case-writer 在生成时可以额外输出：
- 测试数据名称自动加 `tide_test_` 前缀，便于清理
- 测试类的数据隔离方案（若检测到 separated test data 模式）

---

## 4. Skill 编排优化

### 现状

`skills/tide/SKILL.md` 约 200 行，包含从参数校验到验收报告的全部步骤细节，每次调用全量载入。

### 改动方案

Skill 瘦身为三层结构：

```
skills/tide/SKILL.md（~80 行）
│
├── 第 1 层：参数校验 + 环境预检（~15 行）
│   ├── 解析参数（har 路径、--quick、--resume 等）
│   └── 读取 convention-scout.json / convention-fingerprint.yaml
│
├── 第 2 层：Prompt 组装（~20 行）
│   ├── 根据指纹选择加载哪些 prompt 模块
│   ├── 组装核心 prompt 清单
│   └── 成本预估展示
│
├── 第 3 层：波次编排指令（~30 行）
│   ├── 四波次定义（不变）
│   ├── 每波次的 Agent 选择标准
│   └── 波次间数据传递说明
│
└── 第 4 层：验收与归档（~15 行）
    ├── 测试执行命令
    └── 输出格式规范
```

#### 成本预估

在完成 HAR 解析（Wave 1）后，展示预估消耗：

```
╔══════════════════════════════════════╗
║ Tide 成本预估                        ║
║──────────────────────────────────────║
║ 端点数: 24                           ║
║ 场景复杂度: 中等                      ║
║ 预估 tokens: ~192,000 (Wave2+Wave4) ║
║ 预估成本: ~$0.03                     ║
║──────────────────────────────────────║
║ 按 /tide --quick 可跳过交互节省约 30%  ║
╚══════════════════════════════════════╝
```

算法：`端点数 × 场景复杂度系数 × 2（opus wave2 + wave4）`

| 复杂度 | 系数 | 典型场景 |
|--------|------|---------|
| 低 | 3000 tokens/端点 | 纯 CRUD，无复杂业务逻辑 |
| 中 | 8000 tokens/端点 | 有状态机、多步骤流程 |
| 高 | 15000 tokens/端点 | 涉及工作流、数据依赖、跨模块 |

---

## 5. 扩展性架构

### 新增一个项目风格需要几步？

```
以适配"标准 httpx + pydantic 项目"为例：

Step 1: 新增检测器（如已有则跳过）
  scripts/convention_scanner.py 中注册：
    detect_assertion 加 "json_path" 模式
    detect_test_style 加 "conftest_fixture" 模式

Step 2: 新增 prompt 模块
  prompts/code-style-python/30-assert-jsonpath.md     ← 新断言风格
  prompts/code-style-python/40-test-structure-fixture.md  ← 新测试结构

Step 3: 不需要改动的
  convention_scanner.py 主流程 ✓
  tide/SKILL.md 编排逻辑 ✓
  Agent 定义 ✓
  fingerprint.yaml schema ✓（已是通用结构）
```

### 对于非 Python 项目？

tide 当前 pipeline 专为 HAR → pytest 设计。要支持 JS/Go 等语言：

- **需要新 pipeline**：HAR 解析不变，但生成侧需要新语言的 prompt 模块集合
- **共享的部分**：convention_scanner.py 的检测维度逻辑（语言无关的 AST 概念），fingerprint.yaml 的通用 schema
- **不共享的部分**：`prompts/code-style-js/`、新的 case-writer（不同语言）、新的 test runner

建议在本次优化中先不涉及多语言，通过 prompt 模块机制确保 Python 侧的风格扩展性即可。

---

## 6. 不改动的范围

- **Agent 描述**：`agents/*.md` 的职责定义和行为不变，只减少 context 中的 prompt 内容体积
- **Python 脚本接口**：`scripts/*.py` 保持现有函数签名不重构
- **har-parser**：解析逻辑和输出格式不变
- **state-manager/hooks**：不涉及
- **scaffold**：生成流程不变
- **preferences**：偏好系统不变

---

## 7. 成功标准

```
优化完成后的验证清单：

1. Convention 检测
   □ 对 dtstack-httprunner 能准确检测 5 个新增维度
   □ 检测失败时平滑降级，不阻断流程
   □ 输出格式兼容旧版字段

2. Prompt 按需加载
   □ tide/SKILL.md ≤ 100 行
   □ 按指纹加载后，Agent 上下文减少 ≥ 40%
   □ 条件模块的加载/不加载行为正确

3. dtstack 风格适配
   □ 生成的测试代码符合 dtstack 编码规范
   □ 测试代码可被 dtstack 项目 import（语法正确）
   □ Enum 导入、BaseRequests 调用、resp['code'] 断言正确

4. 扩展性
   □ 新增检测器只需追加函数 + 注册
   □ 新增 prompt 模块只需新建文件 + 加载映射
```

---

## 8. 实施顺序

```
Phase 1A: Convention 检测升级
  ├── scripts/convention_scanner.py — 补 5 个检测维度
  └── 测试验证: 对 dtstack-httprunner 输出正确 fingerprint

Phase 1B: Prompt 拆分
  ├── prompts/code-style-python/ 目录拆分（含 _index.md）
  ├── prompts/assertion-layers/ 精简
  ├── prompts/review-checklist.md 精简
  └── prompts/scenario-enrich.md 精简

Phase 1C: dtstack 适配 + 加载逻辑
  ├── 新增 5 个条件 prompt 模块
  ├── tide/SKILL.md 瘦身 + 按需加载逻辑
  ├── 成本预估展示
  └── 端到端测试: HAR → 符合 dtstack 风格的测试代码
```
