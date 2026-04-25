# `/using-tide` 初始化流程重设计 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `/using-tide` 从"平面标签式初始化"升级为"架构感知式初始化"，覆盖多环境、自定义 runner、conftest 链、认证流程、监控体系、模块依赖 6 个企业级维度。

**Architecture:** 3 个顺序子阶段：(2a) convention_scanner.py 新增 6 个检测维度 → (2b) tide-config.yaml schema 扩展 + /using-tide 交互流程增强 → (2c) 新增 3 个 prompt 模块，case-writer 生成适配。

**Tech Stack:** Python 3.12+, AST, YAML, Jinja2

---

## 文件结构

```
Phase 2a — Scanner 6 新维度
  Modify: scripts/convention_scanner.py          ← +6 detect_* 函数
  Test:   tests/test_convention_scanner.py       ← 每个新函数对应测试

Phase 2b — Config + Init 交互
  Modify: scripts/convention_scanner.py          ← scan_project() 集成新维度
  Modify: skills/using-tide/SKILL.md             ← 增强交互流程
  Modify: templates/tide-config.yaml.j2          ← 扩展 schema

Phase 2c — Prompt 模块
  Create: prompts/code-style-python/50-env-config.md
  Create: prompts/code-style-python/55-runner-custom.md
  Create: prompts/code-style-python/60-auth-flow-detailed.md
  Modify: prompts/code-style-python/_index.md    ← 新模块加载规则
```

---

### Task 2a-1: 检测多环境管理

**Files:**
- Modify: `scripts/convention_scanner.py` — 新增 `detect_env_management`
- Test: `tests/test_convention_scanner.py`

- [ ] **Step 1: 实现 `detect_env_management`**

在 `convention_scanner.py` 中添加函数。检测 `config/env/*.ini`、`.env` 文件、`env_config.py` 模式：

```python
def detect_env_management(project_root: Path) -> dict[str, Any]:
    """检测多环境管理模式。"""
    # 检测 config/env/*.ini
    env_dir = project_root / "config" / "env"
    env_files: list[dict[str, str]] = []
    if env_dir.is_dir():
        for f in sorted(env_dir.glob("*.ini")):
            name = f.stem
            env_files.append({"name": name, "file": str(f.relative_to(project_root))})

    # 检测 .env 文件中的 env_file 切换机制
    switch_method = "hardcode"
    env_file_path = project_root / ".env"
    active_env = None
    if env_file_path.exists():
        text = env_file_path.read_text(errors="ignore")
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("env_file") and "=" in line:
                switch_method = "dotenv"
            if not line.startswith("#") and "env_file" in line:
                val = line.split("=", 1)[1].strip()
                active_env = Path(val).stem if val else None

    # 检测 env_config.py 中的 ENV_CONF 模式
    config_module = None
    env_conf_path = project_root / "config" / "env_config.py"
    if env_conf_path.exists():
        text = env_conf_path.read_text(errors="ignore")
        if "ENV_CONF" in text:
            config_module = "config.env_config"

    if not env_files:
        return {"detected": False}

    return {
        "detected": True,
        "count": len(env_files),
        "files": env_files,
        "switch_method": switch_method,
        "active": active_env,
        "config_module": config_module,
    }
```

- [ ] **Step 2: 添加测试**

```python
def test_detect_env_management(self, tmp_path: Path) -> None:
    """检测多环境配置。"""
    env_dir = tmp_path / "config" / "env"
    env_dir.mkdir(parents=True)
    (env_dir / "ci_62.ini").write_text("[base]\nurl=http://ci-62.com\n")
    (env_dir / "ci_63.ini").write_text("[base]\nurl=http://ci-63.com\n")
    env_file = tmp_path / ".env"
    env_file.write_text("env_file = config/env/ci_63.ini\n")

    result = detect_env_management(tmp_path)
    assert result["detected"] is True
    assert result["count"] == 2
    assert result["switch_method"] == "dotenv"
    assert result["active"] == "ci_63"

def test_detect_env_management_no_env(self, tmp_path: Path) -> None:
    """没有多环境配置时返回 detected=False。"""
    result = detect_env_management(tmp_path)
    assert result["detected"] is False
```

- [ ] **Step 3: 运行测试**

Run: `uv run pytest tests/test_convention_scanner.py::TestNewDetectors -v 2>&1 || uv run pytest tests/test_convention_scanner.py -k "env_management" -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add scripts/convention_scanner.py tests/test_convention_scanner.py
git commit -m "feat(scanner): 新增多环境管理检测 — config/env/*.ini + .env 切换机制"
```

---

### Task 2a-2: 检测自定义测试运行器

**Files:**
- Modify: `scripts/convention_scanner.py` — 新增 `detect_test_runner`
- Test: `tests/test_convention_scanner.py`

- [ ] **Step 1: 实现 `detect_test_runner`**

```python
def detect_test_runner(project_root: Path) -> dict[str, Any]:
    """检测自定义测试运行器（run_demo.py、Makefile 等）。"""
    # 检测 run_demo.py / run.py / runner.py
    runner_files = ["run_demo.py", "run.py", "runner.py", "run_tests.py"]
    detected_runner = None
    for rf in runner_files:
        path = project_root / rf
        if path.exists():
            detected_runner = rf
            break

    if not detected_runner:
        return {"type": "pytest_direct", "entry": None}

    # 检测 runner 中的 pytest 参数
    text = (project_root / detected_runner).read_text(errors="ignore")
    options: dict[str, Any] = {"parallel": False, "reruns": 0}

    if "-n " in text:
        options["parallel"] = True
        import re
        m = re.search(r"workers=(\d+)", text)
        if m:
            options["workers"] = int(m.group(1))
    if "--reruns" in text:
        m = re.search(r"rerun=(\d+)", text)
        if m:
            options["reruns"] = int(m.group(1))
    if "alluredir" in text:
        options["report"] = ["allure"]
    if "json-report" in text:
        if "report" in options:
            options["report"].append("json")
        else:
            options["report"] = ["json"]

    # 检测模块级运行入口
    module_entries: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(r'\s+def run_(\w+)_scenariotest\(self\)', line)
        if m:
            module_entries[m.group(1)] = f"python {detected_runner} --module {m.group(1)}"

    return {
        "type": "custom",
        "entry": detected_runner,
        "options": options,
        "module_entries": module_entries if module_entries else None,
    }
```

- [ ] **Step 2: 添加测试**

```python
def test_detect_test_runner(self, tmp_path: Path) -> None:
    runner = tmp_path / "run_demo.py"
    runner.write_text('''
class Run:
    def run_batch_scenariotest(self):
        runner.run_with_option(rerun=1, test_path="...", workers=8)
    def run_stream_scenariotest(self):
        pass
''')
    result = detect_test_runner(tmp_path)
    assert result["type"] == "custom"
    assert result["entry"] == "run_demo.py"
    assert "batch" in result["module_entries"]

def test_detect_test_runner_pytest_direct(self, tmp_path: Path) -> None:
    result = detect_test_runner(tmp_path)
    assert result["type"] == "pytest_direct"
    assert result["entry"] is None
```

- [ ] **Step 3: 运行测试 + 提交**

```bash
uv run pytest tests/test_convention_scanner.py -k "test_runner" -v
git add scripts/convention_scanner.py tests/test_convention_scanner.py
git commit -m "feat(scanner): 新增自定义测试运行器检测 — run_demo.py 参数与模块入口"
```

---

### Task 2a-3: 检测 conftest 链

**Files:**
- Modify: `scripts/convention_scanner.py` — 新增 `detect_conftest_chain`
- Test: `tests/test_convention_scanner.py`

- [ ] **Step 1: 实现 `detect_conftest_chain`**

```python
def detect_conftest_chain(project_root: Path) -> dict[str, Any]:
    """检测 conftest 层级结构和关键 fixture。"""
    conftest_layers: list[dict[str, Any]] = []
    all_fixtures: list[str] = []

    # 扫描项目级 conftest.py
    root_conftest = project_root / "conftest.py"
    if root_conftest.exists():
        fixtures = _extract_fixtures(root_conftest)
        conftest_layers.append({"level": "root", "path": "conftest.py", "fixtures": fixtures})
        all_fixtures.extend(fixtures)

    # 递归扫描 test directories
    for test_dir_name in ["testcases", "tests", "test"]:
        base_dir = project_root / test_dir_name
        if not base_dir.is_dir():
            continue
        for conftest in sorted(base_dir.rglob("conftest.py")):
            rel = str(conftest.relative_to(project_root))
            fixtures = _extract_fixtures(conftest)
            conftest_layers.append({
                "level": "sub",
                "path": rel,
                "fixtures": fixtures,
            })
            all_fixtures.extend(fixtures)

    # 检测特殊 fixture 类型
    fixture_types = _categorize_fixtures(all_fixtures)

    return {
        "layers": conftest_layers,
        "fixture_count": len(all_fixtures),
        "fixture_types": fixture_types,
    }


def _extract_fixtures(conftest_path: Path) -> list[str]:
    """从 conftest.py 提取 fixture 函数名。"""
    try:
        tree = ast.parse(conftest_path.read_text(), filename=str(conftest_path))
    except SyntaxError:
        return []
    fixtures = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for deco in node.decorator_list:
                if (isinstance(deco, ast.Name) and deco.id == "fixture") or \
                   (isinstance(deco, ast.Attribute) and deco.attr == "fixture"):
                    fixtures.append(node.name)
                    break
    return fixtures


def _categorize_fixtures(fixtures: list[str]) -> dict[str, list[str]]:
    """对 fixture 按用途分类。"""
    categories: dict[str, list[str]] = {"auth": [], "data": [], "db": [], "cleanup": [], "other": []}
    for f in fixtures:
        if any(k in f.lower() for k in ["cooki", "token", "auth", "login"]):
            categories["auth"].append(f)
        elif any(k in f.lower() for k in ["data", "init", "create", "ddl"]):
            categories["data"].append(f)
        elif "db" in f.lower():
            categories["db"].append(f)
        elif any(k in f.lower() for k in ["clean", "clear", "teardown", "final"]) or "yield" in f.lower():
            categories["cleanup"].append(f)
        else:
            categories["other"].append(f)
    return {k: v for k, v in categories.items() if v}
```

- [ ] **Step 2: 添加测试**

```python
def test_detect_conftest_chain(self, tmp_path: Path) -> None:
    root = tmp_path / "conftest.py"
    root.write_text("""
import pytest
@pytest.fixture
def client(): ...
@pytest.fixture
def db(): ...
""")
    result = detect_conftest_chain(tmp_path)
    assert len(result["layers"]) >= 1
    assert "client" in result["fixture_types"].get("other", [])
```

- [ ] **Step 3: 运行测试 + 提交**

```bash
uv run pytest tests/test_convention_scanner.py -k "conftest" -v
git add scripts/convention_scanner.py tests/test_convention_scanner.py
git commit -m "feat(scanner): 新增 conftest 链检测 — fixture 抽取与分类"
```

---

### Task 2a-4: 检测认证流程

**Files:**
- Modify: `scripts/convention_scanner.py` — 增强 `detect_auth_method` 为 `detect_auth_flow`
- Test: `tests/test_convention_scanner.py`

- [ ] **Step 1: 将 `detect_auth_method` 增强为 `detect_auth_flow`**

替换现有函数。保持 `detect_auth_method` 兼容性，添加流程检测：

```python
def detect_auth_flow(project_root: Path) -> dict[str, Any]:
    """检测认证流程：认证类、步骤链、凭证来源。"""
    # 基础认证类型检测（保留原 detect_auth_method 逻辑）
    base_result = _detect_auth_type(project_root)
    if base_result["method"] == "none":
        return {**base_result, "flow": None, "auth_class": None}

    # 查找认证类
    auth_class = None
    auth_module = None
    flow_steps: list[str] = []
    credentials_from = None

    for py_file in _iter_py_files(project_root):
        try:
            text = py_file.read_text(errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        # 检测类名含 Cookie/Token/Auth
        if "class BaseCookies" in text or "class BaseToken" in text:
            m = re.search(r"class\s+(\w+)", text)
            if m:
                auth_class = m.group(1)
                auth_module = str(py_file.relative_to(project_root)).replace("/", ".").rstrip(".py")
            # 检测认证步骤
            for step_keyword in ["get_public_key", "encrypt", "login", "refresh"]:
                if re.search(rf"def\s+.*{step_keyword}", text):
                    flow_steps.append(step_keyword)
        if "ENV_CONF" in text and auth_class:
            credentials_from = "env_config"

    if auth_class:
        return {
            "method": base_result["method"],
            "auth_class": auth_class,
            "auth_module": auth_module,
            "flow": flow_steps if flow_steps else None,
            "credentials_from": credentials_from,
        }
    return base_result
```

保留 `_detect_auth_type` 为私有函数，内容来自原 `detect_auth_method`。在 `scan_project` 中将 `detect_auth_method` 替换为 `detect_auth_flow`。

- [ ] **Step 2: 添加测试 + 运行 + 提交**

```python
def test_detect_auth_flow_cookie(self, tmp_path: Path) -> None:
    utils = tmp_path / "utils" / "common"
    utils.mkdir(parents=True)
    auth_file = utils / "get_cookies.py"
    auth_file.write_text('''
class BaseCookies:
    def get_public_key(self): ...
    def login(self): ...
    def refresh(self): ...
from config.env_config import ENV_CONF
''')
    (tmp_path / "conftest.py").write_text("import pytest")
    result = detect_auth_flow(tmp_path)
    assert result["method"] == "cookie"
    assert result["auth_class"] == "BaseCookies"
    assert result["flow"] is not None
```

```bash
uv run pytest tests/test_convention_scanner.py -k "auth_flow" -v
git add scripts/convention_scanner.py tests/test_convention_scanner.py
git commit -m "feat(scanner): 新增认证流程检测 — 认证类/步骤链/凭证来源"
```

---

### Task 2a-5: 检测监控/告警体系

**Files:**
- Modify: `scripts/convention_scanner.py` — 新增 `detect_monitoring`
- Test: `tests/test_convention_scanner.py`

- [ ] **Step 1: 实现 `detect_monitoring`**

```python
def detect_monitoring(project_root: Path) -> dict[str, Any]:
    """检测性能监控与告警体系。"""
    result: dict[str, Any] = {"detected": False}

    for py_file in list(project_root.rglob("*.py"))[:60]:
        if ".venv" in str(py_file) or "__pycache__" in str(py_file):
            continue
        try:
            text = py_file.read_text(errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue

        # 检测性能监控装饰器
        if "calc_request_time_and_alarm" in text or "request_time" in text:
            result["perf_monitor"] = {"pattern": "decorator"}
            m = re.search(r"cost_time\s*>\s*(\d+)", text)
            if m:
                result["perf_monitor"]["threshold_ms"] = int(m.group(1)) * 1000

        # 检测告警通道
        if "send_ding_talk" in text or "dingtalk" in text.lower():
            result.setdefault("alert_channels", []).append("dingtalk")
        if "InfluxDBClient" in text or "influxdb" in text.lower():
            result.setdefault("alert_channels", []).append("influxdb")
        if "write_to_alert_file" in text:
            result["alert_file"] = True

    if result.get("perf_monitor") or result.get("alert_channels"):
        result["detected"] = True
    return result
```

- [ ] **Step 2: 添加测试 + 运行 + 提交**

```python
def test_detect_monitoring(self, tmp_path: Path) -> None:
    base = tmp_path / "utils/common"
    base.mkdir(parents=True)
    (base / "base.py").write_text('''
def calc_request_time_and_alarm(func):
    def wrapper(*args, **kwargs):
        cost_time = 3.5
        if cost_time > 3:
            send_ding_talk("alert")
        return func(*args, **kwargs)
    return wrapper
''')
    result = detect_monitoring(tmp_path)
    assert result["detected"] is True
    assert "dingtalk" in result.get("alert_channels", [])
```

```bash
uv run pytest tests/test_convention_scanner.py -k "monitoring" -v
git add scripts/convention_scanner.py tests/test_convention_scanner.py
git commit -m "feat(scanner): 新增监控/告警体系检测 — 性能装饰器与告警通道"
```

---

### Task 2a-6: 检测模块依赖

**Files:**
- Modify: `scripts/convention_scanner.py` — 新增 `detect_module_dependencies`
- Test: `tests/test_convention_scanner.py`

- [ ] **Step 1: 实现 `detect_module_dependencies`**

```python
def detect_module_dependencies(project_root: Path) -> dict[str, Any]:
    """检测服务模块间依赖关系。"""
    api_dir = project_root / "api"
    if not api_dir.is_dir():
        return {"modules": [], "dependency_graph": None}

    modules: list[dict[str, Any]] = []
    for d in sorted(api_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("__"):
            continue
        module_info: dict[str, Any] = {"name": d.name}
        # 检测对应的 utils
        utils_path = project_root / "utils" / d.name
        if utils_path.is_dir():
            module_info["has_utils"] = True
        # 检测对应的 dao
        dao_path = project_root / "dao" / d.name
        if dao_path.is_dir():
            module_info["has_dao"] = True
        # 检测对应的 test
        test_path = project_root / "testcases" / "scenariotest" / d.name
        if test_path.is_dir():
            module_info["has_tests"] = True
        # 检测对应的 conftest
        module_conftest = test_path / "conftest.py"
        if module_conftest.exists():
            module_info["has_conftest"] = True
        modules.append(module_info)

    return {
        "modules": modules,
        "count": len(modules),
    }
```

- [ ] **Step 2: 注册到 `scan_project`**

在 `scan_project` 返回字典追加：
```python
"modules": detect_module_dependencies(project_root),
```

- [ ] **Step 3: 添加测试 + 运行 + 提交**

```python
def test_detect_module_dependencies(self, tmp_path: Path) -> None:
    for mod in ["batch", "dataapi", "uic"]:
        (tmp_path / "api" / mod).mkdir(parents=True)
        (tmp_path / "api" / mod / "__init__.py").write_text("")
    result = detect_module_dependencies(tmp_path)
    assert result["count"] == 3
    names = [m["name"] for m in result["modules"]]
    assert "batch" in names
```

```bash
uv run pytest tests/test_convention_scanner.py -k "module_dep" -v
git add scripts/convention_scanner.py tests/test_convention_scanner.py
git commit -m "feat(scanner): 新增模块依赖检测 — api/utils/dao/test 映射"
```

---

### Task 2b-1: tide-config.yaml 模板扩展

**Files:**
- Modify: `templates/tide-config.yaml.j2`

- [ ] **Step 1: 更新模板**

扩展当前模板，新增 environments、modules、test_runner、auth_flow、monitoring 节：

```yaml
# tide-config.yaml — 由 /using-tide 自动生成

project:
  name: "{{ project_name | default('') }}"
  type: {{ project_type }}  # existing | new
  complexity: {{ complexity | default('simple') }}  # simple | moderate | complex
  {% if python_version %}
  python_version: {{ python_version }}
  {% endif %}
  {% if test_framework %}
  test_framework: {{ test_framework }}
  {% endif %}

# ---------- 代码规范 ----------
code_style:
  api_pattern: {{ api_pattern | default('inline') }}
  {% if http_client %}
  http_client:
    type: {{ http_client.type }}
    {% if http_client.custom_class %}
    custom_class: {{ http_client.custom_class }}
    {% endif %}
  {% endif %}
  {% if assertion_style %}
  assertion_style: {{ assertion_style }}
  {% endif %}
  {% if test_structure %}
  test_structure:
    file_suffix: {{ test_structure.file_suffix | default('test_*.py') }}
    fixture_style: {{ test_structure.fixture_style | default('conftest_fixture') }}
  {% endif %}

# ---------- 环境（仅 detected=true 时）----------
{% if environments and environments.detected %}
environments:
  files:
    {% for env in environments.files %}
    - { name: {{ env.name }}, file: {{ env.file }} }
    {% endfor %}
  active: {{ environments.active | default('') }}
  switch_method: {{ environments.switch_method | default('hardcode') }}
  {% if environments.config_module %}
  config_module: {{ environments.config_module }}
  {% endif %}
{% endif %}

# ---------- 测试运行器（仅 type=custom 时）----------
{% if test_runner and test_runner.type == 'custom' %}
test_runner:
  entry: {{ test_runner.entry }}
  options:
    parallel: {{ test_runner.options.parallel | default('false') }}
    {% if test_runner.options.workers %}
    default_workers: {{ test_runner.options.workers }}
    {% endif %}
    reruns: {{ test_runner.options.reruns | default(0) }}
  {% if test_runner.module_entries %}
  module_entries:
    {% for module, command in test_runner.module_entries.items() %}
    {{ module }}: {{ command }}
    {% endfor %}
  {% endif %}
{% endif %}

# ---------- 认证（仅 method != none 时）----------
{% if auth and auth.method != 'none' %}
auth:
  method: {{ auth.method }}
  {% if auth.auth_class %}
  class: {{ auth.auth_class }}
  {% if auth.auth_module %}
  module: {{ auth.auth_module }}
  {% endif %}
  {% endif %}
  {% if auth.flow %}
  flow:
    {% for step in auth.flow %}
    - {{ step }}
    {% endfor %}
  {% endif %}
{% endif %}

# ---------- 监控（仅 detected=true 时）----------
{% if monitoring and monitoring.detected %}
monitoring:
  {% if monitoring.perf_monitor %}
  performance:
    threshold_ms: {{ monitoring.perf_monitor.threshold_ms | default(3000) }}
  {% endif %}
  {% if monitoring.alert_channels %}
  alerts: {{ monitoring.alert_channels | join(', ') }}
  {% endif %}
{% endif %}
```

- [ ] **Step 2: 提交**

```bash
git add templates/tide-config.yaml.j2
git commit -m "feat(config): 扩展 tide-config.yaml 模板 — 多环境/runner/认证/监控"
```

---

### Task 2b-2: /using-tide 交互流程增强

**Files:**
- Modify: `skills/using-tide/SKILL.md`

- [ ] **Step 1: 在初始化步骤中新增复杂度分支**

在现有"环境检测 + 智能分类"步骤后，追加复杂度评估和多环境检测：

```markdown
### 增强后流程（新增部分用 ★ 标记）

1. 环境检测 + 智能分类（保持不变）
2. ★ **复杂度评估**：
   - 运行 `uv run python3 scripts/convention_scanner.py --project-root .`
   - 读取输出，评估：
     - 模块数 > 3 → complexity = complex
     - 有 config/env/*.ini → complexity = complex
     - 有 run_demo.py → complexity = moderate
     - 否则 → complexity = simple
3. 深度扫描（保持不变，但扫描输出更丰富）
4. ★ **多环境检测确认**（仅 complexity=moderate/complex）：
   - 展示检测到的环境列表
   - 询问：是否配置多环境？当前默认环境是哪个？
   - 若确认，写入 environments 节到 tide-config.yaml
5. ★ **测试运行器检测**（complexity=complex）：
   - 若检测到 run_demo.py 等自定义 runner：
     - 展示检测到的运行参数（并行数、重试次数）
     - 展示模块级运行入口
     - 确认写入 tide-config.yaml
6. ★ **认证流程确认**（如有认证类）：
   - 展示检测到的认证方式 + 认证类 + 步骤链
   - 确认凭证来源
7. 仓库配置 + 连接配置（保持不变）
8. 配置验证（保持不变）
```

- [ ] **Step 2: 更新验收命令生成**

当检测到自定义 runner 时，验收命令改为适配 runner 而非裸 pytest：

```markdown
### 验收命令生成

若 tide-config.yaml 中存在 test_runner.type == custom：
  - 展示：`python {{ test_runner.entry }}` 运行全部测试
  - 展示：`python {{ test_runner.entry }} --module <name>` 运行特定模块
若没有自定义 runner：
  - 现有 pytest 命令逻辑
```

- [ ] **Step 3: 提交**

```bash
git add skills/using-tide/SKILL.md
git commit -m "feat(init): /using-tide 增强 — 复杂度评估/多环境/自定义 runner 确认"
```

---

### Task 2c-1: 新增 3 个条件 prompt 模块

**Files:**
- Create: `prompts/code-style-python/50-env-config.md`
- Create: `prompts/code-style-python/55-runner-custom.md`
- Create: `prompts/code-style-python/60-auth-flow-detailed.md`
- Modify: `prompts/code-style-python/_index.md`

- [ ] **Step 1: 创建 `50-env-config.md`**

```markdown
# 多环境配置规范

> 当 fingerprint.env_management.detected == true 时加载

## 规则

1. Base URL 必须从环境的配置模块读取，不得硬编码
2. 使用 `ENV_CONF.base_url.{module}` 或等价方式获取 URL
3. 枚举值、数据库连接等环境相关配置也通过 ENV_CONF 获取

## 示例

```python
# 正确：从环境配置读取
from config.env_config import ENV_CONF
from api.batch.batch_api import BatchApi

url = ENV_CONF.base_url.rdos + BatchApi.create_project.value

# 错误：硬编码
url = "http://172.16.122.52:82" + "/api/rdos/..."
```

## 切换环境

用户通过 `.env` 文件或环境变量切换环境，测试代码无需修改。
```

- [ ] **Step 2: 创建 `55-runner-custom.md`**

```markdown
# 自定义测试运行器规范

> 当 fingerprint.test_runner.type == "custom" 时加载

## 规则

1. 不生成裸 pytest 命令作为验收命令
2. 使用项目已有的测试运行器（run_demo.py 等）来运行测试
3. 按模块入口组织验收命令

## 示例

```bash
# 运行全部测试
python run_demo.py

# 运行特定模块
python run_demo.py --module batch
python run_demo.py --module dataapi
```
```

- [ ] **Step 3: 创建 `60-auth-flow-detailed.md`**

```markdown
# 多步认证流程规范

> 当 fingerprint.auth.flow 存在且包含多个步骤时加载

## 规则

1. 测试代码应复用项目已有的认证类，而非自行实现认证
2. 在测试类的 `setup_class` 或会话 fixture 中实例化认证类
3. 若认证类自动在 HTTP 客户端构造时注入，测试代码无需额外处理

## 示例

```python
# 认证已由 BaseRequests.__init__ 自动处理
from utils.common.BaseRequests import BaseRequests

class TestFeature:
    def setup_class(self):
        self.req = BaseRequests()  # 自动注入 cookie

    def test_something(self):
        resp = self.req.post(url, "描述", json={...})
```

## 凭证来源

认证凭据从 ENV_CONF 或 .env 读取，测试代码不应包含明文凭据。
```

- [ ] **Step 4: 更新 `_index.md`**

追加加载规则到 `prompts/code-style-python/_index.md`：

```markdown
| 条件 | 加载模块 |
|------|---------|
| fingerprint.env_management.detected == true | `50-env-config.md` |
| fingerprint.test_runner.type == "custom" | `55-runner-custom.md` |
| fingerprint.auth.flow 包含多步 | `60-auth-flow-detailed.md` |
```

- [ ] **Step 5: 提交**

```bash
git add prompts/code-style-python/
git commit -m "feat(prompts): 新增 3 个条件模块 — 多环境/自定义 runner/认证流程"
```

---

### Task 2c-2: dtstack 端到端验证

**Files:**
- Validate: dtstack-httprunner 项目全流程

- [ ] **Step 1: 扫描 dtstack 项目验证新维度**

```bash
uv run python3 scripts/convention_scanner.py \
  --project-root /Users/poco/Projects/dtstack-httprunner \
  --output /tmp/dtstack-phase2.json

python3 -c "
import json
d = json.load(open('/tmp/dtstack-phase2.json'))
print('=== 多环境 ===')
print(d.get('env_management'))
print()
print('=== 自定义 Runner ===')
print(d.get('test_runner'))
print()
print('=== 认证流程 ===')
print(d.get('auth'))
print()
print('=== 监控 ===')
print(d.get('monitoring'))
print()
print('=== 模块 ===')
print(d.get('modules'))
"
```

Expected: 所有新检测维度都有数据

- [ ] **Step 2: 运行全部测试**

```bash
uv run pytest tests/ -q
```

Expected: 所有测试通过

- [ ] **Step 3: 提交**

```bash
git add -A
git commit -m "chore: Phase 2 init redesign — 扫描增强/配置扩展/生成适配"
```
