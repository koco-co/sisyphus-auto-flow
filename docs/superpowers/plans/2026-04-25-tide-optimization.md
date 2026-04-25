# Tide 全面优化实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 提升 tide 在企业级接口自动化项目中的生成质量、运行效率与扩展性，以 dtstack-httprunner 为首个验证目标。

**Architecture:** 扩展 convention_scanner.py 的检测维度 → 将 prompts/ 拆为核心+条件模块按需加载 → 新增 dtstack 风格 prompt 模块 → 编写 case-writer 从 convention-fingerprint.yaml 读取指纹驱动代码生成。

**Tech Stack:** Python 3.12+, AST, pytest

---

## 文件结构

```
Phase 1A — Convention 检测升级
  Modify: scripts/convention_scanner.py           ← 新增 detect_test_style, detect_allure_detail; 增强 detect_http_client, detect_assertion_style
  Test:   tests/test_convention_scanner.py        ← 新增测试（可用 dtstack 项目作为验证目标）

Phase 1B — Prompt 重构
  Delete:  prompts/code-style-python.md           ← 拆分为以下模块
  Create:  prompts/code-style-python/_index.md    ← 模块清单（供 skill 读取）
  Create:  prompts/code-style-python/00-core.md   ← 通用规范（源自原有文件第 1、8-13 节）
  Create:  prompts/code-style-python/10-api-enum.md         ← Enum 风格 API 规范
  Create:  prompts/code-style-python/10-api-class.md        ← Class 风格 API 规范
  Create:  prompts/code-style-python/10-api-inline.md       ← 内联 URL 规范
  Create:  prompts/code-style-python/20-client-custom.md    ← 自定义客户端调用规范
  Create:  prompts/code-style-python/20-client-httpx.md     ← httpx 客户端规范
  Create:  prompts/code-style-python/20-client-requests.md  ← requests 客户端规范
  Create:  prompts/code-style-python/30-assert-code-success.md   ← resp['code'] == 1 断言
  Create:  prompts/code-style-python/30-assert-status-only.md    ← status_code 断言
  Create:  prompts/code-style-python/40-test-structure-dtstack.md  ← _test.py + setup_class
  Create:  prompts/code-style-python/40-test-structure-standard.md ← conftest fixture 模式
  Modify:  prompts/assertion-layers.md              ← 精简至核心定义
  Modify:  prompts/review-checklist.md              ← 精简至核心评审标准
  Modify:  prompts/scenario-enrich.md               ← 精简至核心场景策略

Phase 1C — dtstack 适配 + 加载逻辑
  Modify:  skills/tide/SKILL.md                     ← 瘦身 + 按需加载逻辑 + 成本预估
  Test:   End-to-end: HAR → 符合 dtstack 风格的测试代码
```

---

### Task 1: 增强 convention_scanner.py — HTTP 客户端检测

**Files:**
- Modify: `scripts/convention_scanner.py:114-190`
- Test: `tests/test_convention_scanner.py`（追加）

当前 `detect_http_client` 能检测出 imports 统计和基本自定义类名，但缺少方法签名和模块路径信息——这是 case-writer 生成正确导入语句的关键。

- [ ] **Step 1: 在 detect_http_client 中追加方法签名检测**

在原有检测代码之后（定位到自定义类），追加检测该自定义类的 post/get 方法签名：

```python
def _detect_client_method_signature(
    tree: ast.Module,
    class_name: str,
) -> dict[str, Any] | None:
    """检测自定义客户端的 HTTP 方法签名。"""
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "post":
                    args = [ast.unparse(a) for a in item.args.args]
                    return {
                        "has_desc_param": "desc" in args,
                        "signature": f"post({', '.join(args)})",
                    }
    return None
```

在 `detect_http_client` 的返回结果中追加字段：

```python
result["custom_class_detail"] = {
    "name": class_name,
    "module": module_path,
    "method": method_info,
}
```

- [ ] **Step 2: 添加模块路径检测**

在 `detect_http_client` 中，识别出自定义 request/client 类时同时记录文件路径。由于当前函数一次性遍历全部文件，需要将检测逻辑改为"先收集所有 parsed 文件，再分类检测"：

```python
# 改造 detect_http_client 开头，收集 parsed 文件列表
parsed_files: list[tuple[Path, ast.Module]] = []
for py_file in _iter_py_files(project_root):
    try:
        text = py_file.read_text()
    except (OSError, UnicodeDecodeError):
        continue
    tree = _parse_ast(text, filename=str(py_file))
    if tree is not None:
        parsed_files.append((py_file, tree))

# 用 parsed_files 替代原有的 _iter_py_files 循环进行所有检测
for py_file, tree in parsed_files:
    # ... imports 统计（用 ast 而非字符串搜索）...

for py_file, tree in parsed_files:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and ("request" in node.name.lower() or "client" in node.name.lower()):
            for item in ast.walk(node):
                if isinstance(item, ast.FunctionDef) and item.name in _http_methods:
                    custom_class_name = node.name
                    rel_path = str(py_file.relative_to(project_root))
                    method_sig = _detect_client_method_signature(tree, custom_class_name)
                    # 在返回结果中追加 custom_class_detail
                    return {
                        "library": lib,
                        "client_pattern": "custom_class",
                        "custom_class": custom_class_name,
                        "custom_class_detail": {
                            "name": custom_class_name,
                            "module": rel_path.replace("/", ".").rstrip(".py"),
                            "method": method_sig,
                        },
                    }
```

- [ ] **Step 3: 运行现有测试确保不破坏行为**

Run: `uv run pytest tests/test_convention_scanner.py -v`

Expected: All existing tests PASS

- [ ] **Step 4: 提交**

```bash
git add scripts/convention_scanner.py tests/test_convention_scanner.py
git commit -m "feat(convention): 增强 HTTP 客户端检测 — 方法签名与模块路径"
```

---

### Task 2: 增强 convention_scanner.py — 断言风格检测

**Files:**
- Modify: `scripts/convention_scanner.py:193-229`

当前 `detect_assertion_style` 仅能识别 `dict_get`/`bracket`/`attr`/`status_only` 四种风格。dtstack 的 `resp["code"] == 1, resp["message"]` 被误记为 `bracket`，但 `code_success` 模式（断言 code==1 且 success==True）是一个有意义的独立风格。

- [ ] **Step 1: 添加 `import re` 到文件头部**

```python
import argparse
import ast
import json
import re  # 新增
from datetime import UTC, datetime
```

- [ ] **Step 2: 添加 `code_success` 检测模式**

在 `detect_assertion_style` 的 assert-walk 循环中，新增统计：

```python
# 在 assert 遍历的循环体中追加
if node.test and isinstance(node.test, ast.Compare):
    source = ast.unparse(node.test)
    # 检测 resp["code"] == 1、result["code"] == 0 等
    if "\"code\"" in source or "'code'" in source:
        # 检查是否伴随 success 断言
        counts["code_success"] = counts.get("code_success", 0) + 1
```

同时添加辅助方法检测——扫描测试文件中是否调用了 `assert_response_json`、`assert_response_success` 等方法：

```python
def _detect_assertion_helpers(test_dir: Path) -> list[str]:
    """扫描测试文件或 utils 中定义的辅助断言方法。"""
    helpers = []
    for py_file in list(test_dir.rglob("*.py"))[:20]:
        try:
            text = py_file.read_text(errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        for match in re.finditer(r"def (assert_\w+)\(self", text):
            helpers.append(match.group(1))
    return helpers
```

- [ ] **Step 3: 在返回结果中补充 helper_methods 字段**

```python
return {
    "style": dominant,
    "common_checks": samples,
    "helper_methods": helpers,  # 新增
}
```

- [ ] **Step 4: 运行测试验证**

Run: `uv run pytest tests/test_convention_scanner.py -v`

- [ ] **Step 5: 提交**

```bash
git add scripts/convention_scanner.py
git commit -m "feat(convention): 新增断言风格 code_success 检测 + 辅助方法扫描"
```

---

### Task 3: 新增 convention_scanner.py — 测试风格检测

**Files:**
- Modify: `scripts/convention_scanner.py` — 新增 `detect_test_style` 函数
- Modify: `scripts/convention_scanner.py` — 在 `scan_project` 中注册

- [ ] **Step 1: 实现 `detect_test_style` 函数**

```python
def detect_test_style(project_root: Path) -> dict[str, Any]:
    """检测测试风格：文件命名、fixture 模式、pytest markers。"""
    test_dir_candidates = [
        project_root / "testcases",
        project_root / "tests",
        project_root / "test",
    ]
    test_dir = next((d for d in test_dir_candidates if d.is_dir()), None)
    if not test_dir:
        return {"file_suffix": "test_*.py", "fixture_style": "unknown", "markers": []}

    # 文件后缀检测
    test_underscore = len(list(test_dir.rglob("*_test.py")))
    test_prefix = len(list(test_dir.rglob("test_*.py")))

    # fixture 风格检测
    conftest_files = list(test_dir.rglob("conftest.py"))
    has_setup_class = False
    for cf in conftest_files[:3]:
        text = cf.read_text(errors="ignore")
        if "setup_class" in text or "setup_method" in text:
            has_setup_class = True

    # Marker 检测
    markers: list[str] = []
    pytest_ini = project_root / "pytest.ini"
    if pytest_ini.exists():
        text = pytest_ini.read_text()
        for line in text.splitlines():
            m = re.match(r"\s+(\w+):", line)
            if m:
                markers.append(m.group(1))

    return {
        "file_suffix": "*_test.py" if test_underscore > test_prefix else "test_*.py",
        "fixture_style": "setup_class" if has_setup_class else "conftest_fixture",
        "markers": markers,
    }
```

在 `scan_project` 的返回字典中追加：

```python
return {
    ...
    "test_style": detect_test_style(project_root),
}
```

- [ ] **Step 2: 运行 dtstack 验证**

Run: `uv run python3 scripts/convention_scanner.py --project-root /Users/poco/Projects/dtstack-httprunner`

Expected: 输出中 `test_style` 字段显示 `file_suffix: "*_test.py"`, `markers` 包含 `["smoke", "kerberos", "tpcds", "cdp", "cdh"]`

- [ ] **Step 3: 提交**

```bash
git add scripts/convention_scanner.py
git commit -m "feat(convention): 新增 test_style 检测 — 文件命名/fixture 模式/markers"
```

---

### Task 4: 新增 convention_scanner.py — Allure 详情检测

**Files:**
- Modify: `scripts/convention_scanner.py` — 在 `detect_allure_pattern` 中追加字段

- [ ] **Step 1: 增强 detect_allure_pattern**

追加对 attach 方式和 feature/story 层级的检测：

```python
def detect_allure_pattern(project_root: Path) -> dict[str, Any]:
    """检测 Allure 使用模式。"""
    # ... 保留原有检测代码 ...

    # 新增：检测 attach 方式
    attach_on_request = False
    allure_feature_values: set[str] = set()
    allure_story_values: set[str] = set()

    for py_file in list(project_root.rglob("*.py"))[:50]:
        if ".venv" in str(py_file) or "__pycache__" in str(py_file):
            continue
        try:
            text = py_file.read_text(errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        if "allure.attach" in text:
            attach_on_request = True
        for m in re.finditer(r'@allure\.feature\("([^"]+)"\)', text):
            allure_feature_values.add(m.group(1))
        for m in re.finditer(r'@allure\.story\("([^"]+)"\)', text):
            allure_story_values.add(m.group(1))

    result = {
        # ... 保留原有返回字段 ...
    }

    # 追加新增字段
    if enabled:
        result["attach_on_request"] = attach_on_request
        result["feature_names"] = sorted(allure_feature_values) if allure_feature_values else None
        result["story_names"] = sorted(allure_story_values) if allure_story_values else None

    return result
```

- [ ] **Step 2: 运行 dtstack 验证**

Run: `uv run python3 scripts/convention_scanner.py --project-root /Users/poco/Projects/dtstack-httprunner`

Expected: `allure.attach_on_request` 为 `true`

- [ ] **Step 3: 提交**

```bash
git add scripts/convention_scanner.py
git commit -m "feat(convention): 增强 Allure 检测 — attach 方式/feature 层级"
```

---

### Task 5: 拆分 prompts/code-style-python.md 为核心 + 条件模块

**Files:**
- Delete: `prompts/code-style-python.md`
- Create: `prompts/code-style-python/_index.md`
- Create: `prompts/code-style-python/00-core.md`
- Create: `prompts/code-style-python/10-api-enum.md`
- Create: `prompts/code-style-python/10-api-class.md`
- Create: `prompts/code-style-python/10-api-inline.md`
- Create: `prompts/code-style-python/20-client-custom.md`
- Create: `prompts/code-style-python/20-client-httpx.md`
- Create: `prompts/code-style-python/20-client-requests.md`
- Create: `prompts/code-style-python/30-assert-code-success.md`
- Create: `prompts/code-style-python/30-assert-status-only.md`
- Create: `prompts/code-style-python/40-test-structure-dtstack.md`
- Create: `prompts/code-style-python/40-test-structure-standard.md`
- Modify: `prompts/assertion-layers.md` — 精简
- Modify: `prompts/review-checklist.md` — 精简
- Modify: `prompts/scenario-enrich.md` — 精简

- [ ] **Step 1: 创建 `_index.md` 模块清单**

```markdown
# code-style-python 模块索引

> 由 tide/SKILL.md 按需读取，根据 convention-fingerprint.yaml 决定加载哪些模块。

## 加载规则

| 条件 | 加载模块 | 说明 |
|------|---------|------|
| 始终 | `00-core.md` | 通用规范 |
| fingerprint.api.type == "enum" | `10-api-enum.md` | Enum 风格 API |
| fingerprint.api.type == "class" | `10-api-class.md` | Class 风格 API |
| fingerprint.api.type in ("inline", null) | `10-api-inline.md` | 内联 URL |
| fingerprint.http_client.client_pattern == "custom_class" | `20-client-custom.md` | 自定义 HTTP 客户端 |
| fingerprint.http_client.library == "httpx" | `20-client-httpx.md` | httpx 客户端 |
| fingerprint.http_client.library == "requests" | `20-client-requests.md` | requests 客户端 |
| fingerprint.assertion.style == "code_success" | `30-assert-code-success.md` | resp["code"]==1 断言 |
| fingerprint.assertion.style in ("status_only", null) | `30-assert-status-only.md"` | status_code 断言 |
| fingerprint.test_style.file_suffix == "*_test.py" | `40-test-structure-dtstack.md` | _test.py + setup_class |
| fingerprint.test_style not in ("*_test.py", null) | `40-test-structure-standard.md` | test_*.py + conftest |
```

- [ ] **Step 2: 创建 `00-core.md`**

从原 `code-style-python.md` 提取第 1 节（文件结构）、第 8-13 节（不可变性、规模限制、禁止模式、导入规范、类型注解、检查清单）。共约 60 行。

```markdown
# Python 测试代码风格指南 — 核心规范

> 所有生成代码都必须遵守此文档

## 1. 文件结构

每个生成的测试文件按以下从上到下的顺序组织——不得例外：

```python
"""模块文档字符串"""
# 1. 标准库导入
# 2. 第三方库导入（组内按字母顺序）
# 3. 内部导入
# 4. 常量
# 5. 模型定义
# 6. 测试类
```

## 2. 不可变性

- 值对象使用 `@dataclass(frozen=True)` 或 `BaseModel`（Pydantic）
- 绝不修改 fixture 对象——创建新对象

## 3. 规模限制

- 文件 ≤ 400 行
- 测试方法 ≤ 50 行
- Fixture ≤ 30 行
- 嵌套深度 ≤ 4 层

## 4. 禁止模式

- 禁止硬编码值（已命名的常量除外）
- 禁止 `print()` 语句（使用 `allure.attach` 替代）
- 禁止深层嵌套（用提前返回/辅助方法展平）
- 禁止修改共享状态
- 禁止直接写入 DB（通过 API 创建和清理数据）

## 5. 导入规范

标准库 → 第三方库 → 内部导入，分组间空行。绝不使用 `from module import *`。

## 6. 类型注解

所有函数签名必须包含类型注解。

## 7. 完成文件前的快速检查清单

- [ ] 文件以模块文档字符串开头
- [ ] 所有导入已按规范组织
- [ ] 所有常量已在模块级命名定义
- [ ] 无 `print()` 语句
- [ ] 文件不超过 400 行
- [ ] 每个测试方法不超过 50 行
- [ ] 所有函数有类型注解
```

- [ ] **Step 3: 创建 `10-api-enum.md`**

```markdown
# Enum 风格 API 规范

> 当 fingerprint.api.type == "enum" 时加载

## 规则

1. 从 fingerprint.api.modules 中找出对应接口的 Enum 类
2. URL 必须通过 `{EnumClass}.{member}.value` 引用，不得硬编码字符串
3. 完整 URL 为 `{base_url}{EnumClass.{member}.value}`

## 示例

```python
from api.batch.batch_api import BatchApi
url = ENV_CONF.base_url + BatchApi.create_project.value
```
```

- [ ] **Step 4: 创建 `20-client-custom.md`**

```markdown
# 自定义 HTTP 客户端调用规范

> 当 fingerprint.http_client.client_pattern == "custom_class" 时加载

## 规则

1. 从 fingerprint.http_client.custom_class_detail 读取类名和模块路径
2. 在 `setup_class` 中实例化：`self.client = {ClassName}()`
3. 调用方法签名匹配检测到的签名：`self.client.{method}(url, desc, **kwargs)`
4. 不使用 httpx/requests 裸调用

## 示例

```python
from utils.common.BaseRequests import BaseRequests

class TestCreateProject:
    def setup_class(self):
        self.req = BaseRequests()

    def test_create_project(self):
        url = ENV_CONF.base_url + BatchApi.create_project.value
        resp = self.req.post(url, "新建项目", json=params)
```

## Attach

若 fingerprint.allure.attach_on_request 为 true，自定义客户端已自动处理 allure attach，
不需在测试方法中手动 attach。
```

- [ ] **Step 5: 创建 `30-assert-code-success.md`**

```markdown
# resp["code"] == 1 断言规范

> 当 fingerprint.assertion.style == "code_success" 时加载

## 规则

1. 主要断言：`assert resp["code"] == 1, resp["message"]`
2. 成功断言：`assert resp["success"] is True`
3. 若有 helper_methods（如 `assert_response_success`），优先使用辅助方法

## 示例

```python
# 直接断言
resp = self.req.post(url, "新建项目", json=params)
assert resp["code"] == 1, resp["message"]
assert resp["success"] is True

# 使用辅助方法
self.req.assert_response_success()
```
```

- [ ] **Step 6: 创建剩下条件模块**

创建 `10-api-class.md`、`10-api-inline.md`、`20-client-httpx.md`、`20-client-requests.md`、`30-assert-status-only.md`、`40-test-structure-dtstack.md`、`40-test-structure-standard.md`。每个文件约 10-20 行，格式同上。

- [ ] **Step 7: 删除原 `code-style-python.md`**

```bash
git rm prompts/code-style-python.md
```

- [ ] **Step 8: 精简 `prompts/assertion-layers.md`**

移除第 3-5 节中冗长的示例代码（原文件 430 行），只保留核心定义和矩阵，压缩至 ~80 行。保留：
- 断言层与测试类型矩阵
- 各层的一两句话定义 + 核心规则表
- 代码模式从示例简化为"参考 core.md"
- 移除完整的 assert_protocol 实现、长 Pydantic 模型示例、详细 DB 断言说明

- [ ] **Step 9: 精简 `prompts/review-checklist.md`**

移除第 3 节（源码交叉验证——这不是 review 的职责）、压缩第 4 节和第 5 节的长篇示例，从 ~300 行减至 ~80 行。保留：
- 检查矩阵（断言完整性/场景完整性/代码质量/可运行性）
- 偏差阈值与修正动作
- 报告输出格式
- 移除：源码 grep 命令引用、详细的 DB 断言检查说明

- [ ] **Step 10: 精简 `prompts/scenario-enrich.md`**

从 ~430 行精简至 ~60 行。保留：
- 源码分析策略的框架
- 8 种场景类别列表
- assertion_layers 矩阵引用
- 移除：大量 Java 示例代码、逐方法的详细说明

- [ ] **Step 11: 提交**

```bash
git add prompts/
git rm prompts/code-style-python.md
git commit -m "refactor(prompts): 拆分 code-style-python 为核心+条件模块，精简 assertion-layers/review-checklist/scenario-enrich"
```

---

### Task 6: 更新 tide/SKILL.md — 按需加载逻辑 + 成本预估

**Files:**
- Modify: `skills/tide/SKILL.md`

- [ ] **Step 1: 在预检阶段追加 prompt 按需加载步骤**

将第 7 步"惯例指纹加载"扩展为：

```markdown
7. **惯例指纹加载 + Prompt 组装**：
   test -f .tide/convention-fingerprint.yaml && echo "FINGERPRINT_EXISTS" || echo "NO_FINGERPRINT"
   若 fingerprint 存在：
   - 读取 .tide/convention-fingerprint.yaml
   - 读取 prompts/code-style-python/_index.md 获取加载规则
   - 根据 fingerprint 字段值选择加载哪些 prompt 模块
   - 将选定模块的内容作为后续 Agent 的"项目规范"约束段
   - 设置 fingerprint_mode=true
   若不存在：
   - 加载 prompts/code-style-python/00-core.md + 20-client-httpx.md + 30-assert-status-only.md + 40-test-structure-standard.md
   - 设置 fingerprint_mode=false
```

- [ ] **Step 2: 追加成本预估展示**

在第 11 步"参数摘要"后，当 `fingerprint_mode=true` 时展示：

```markdown
12. **成本预估**：
   端点数：har-parser 输出中的 endpoint 数量
   - 端点数 ≤ 10 → 复杂度"低"
   - 端点数 11-30 → 复杂度"中"
   - 端点数 > 30 → 复杂度"高"
   预估 tokens = 端点数 × 复杂度系数 × 2（wave2+wave4 用 opus）
   展示格式：
   ```
   ╔══════════════════════════════════════╗
   ║ Tide 成本预估                        ║
   ║──────────────────────────────────────║
   ║ 端点数: N                            ║
   ║ 场景复杂度: 低/中/高                  ║
   ║ 预估 tokens: ~X                      ║
   ║ 预估成本: ~$Y                        ║
   ╚══════════════════════════════════════╝
   ```
   询问用户是否继续。
```

- [ ] **Step 3: 检查当前 SKILL.md 是否满足 ≤ 100 行**

Run: `wc -l skills/tide/SKILL.md`

Expected: 约 80-100 行

- [ ] **Step 4: 提交**

```bash
git add skills/tide/SKILL.md
git commit -m "feat(skill): 按需 prompt 加载 + 成本预估"
```

---

### Task 7: 端到端验证

**Files:**
- Validate: 对 dtstack-httprunner 项目运行 tide scanner，检查 output
- Validate: 确认 prompt 按需加载行为正确

- [ ] **Step 1: 对 dtstack 运行 convention scanner**

Run:
```bash
uv run python3 scripts/convention_scanner.py \
  --project-root /Users/poco/Projects/dtstack-httprunner \
  --output /tmp/dtstack-scout.json
cat /tmp/dtstack-scout.json | python3 -c "import json,sys; d=json.load(sys.stdin); print('test_style:', d.get('test_style')); print('assertion helpers:', d['assertion'].get('helper_methods')); print('allure attach:', d['allure'].get('attach_on_request'))"
```

Expected: `test_style` 包含 `file_suffix: "*_test.py"` 和 markers 列表，`assertion.helper_methods` 包含 `assert_response_success`，`allure.attach_on_request` 为 `true`

- [ ] **Step 2: 检查 prompt 模块文件完整性**

Run: `ls prompts/code-style-python/`

Expected: `_index.md`, `00-core.md`, `10-api-enum.md`, `10-api-class.md`, `10-api-inline.md`, `20-client-custom.md`, `20-client-httpx.md`, `20-client-requests.md`, `30-assert-code-success.md`, `30-assert-status-only.md`, `40-test-structure-dtstack.md`, `40-test-structure-standard.md` — 共 12 个文件

- [ ] **Step 3: 汇总并输出完成报告**

```bash
echo "=== Files changed ==="
git diff --stat HEAD~3..HEAD
echo "=== Verification ==="
uv run python3 scripts/convention_scanner.py --project-root /Users/poco/Projects/dtstack-httprunner --output /dev/null 2>&1
echo "=== Prompt module count ==="
ls prompts/code-style-python/*.md | wc -l
```

- [ ] **Step 4: 提交**

```bash
git add -A
git commit -m "chore: tide 全面优化 Phase 1 完成 — 检测升级 + prompt 按需加载 + dtstack 适配"
```
