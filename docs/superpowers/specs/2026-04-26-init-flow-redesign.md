# `/using-tide` 初始化流程重设计

**日期**: 2026-04-26
**状态**: 调研分析

---

## 一、dtstack-httprunner 被忽略的场景（12 项）

以 dtstack-httprunner 为样本，以下是 `/using-tide` 初始化时完全没有覆盖的方面：

### 1. 多环境管理
- 9 个 `.ini` 文件在 `config/env/`，代表 9 套环境（ci_52/62/63、dm_63、test_63 等）
- `.env` 文件通过注释/取消注释行切换环境
- `ENV_CONF.base_url.{module}` 是标准的 Base URL 访问方式
- 当前 tide 只记录了"一个" Base URL

### 2. 自定义测试运行器
- `run_demo.py` 包含 `Run` 类，封装了 pytest 参数
- 支持并行（xdist）、重试、报告生成、旧结果清理
- 不同模块有不同的运行入口方法
- tide 生成的验收命令（`pytest tests/...`）与此不匹配

### 3. 复杂 conftest 体系
- 项目根 conftest 有 `pytest_terminal_summary` 自定义统计
- 子模块 conftest（scenariotest）有全局 fixture：告警机制（DingTalk + InfluxDB）、数据源动态加载、初始化数据链
- xdist 感知：FileLock 跨进程同步、共享临时目录
- Allure + JSON 双报告

### 4. 多模块服务架构
- 11 个 API 模块，各自有独立的 utils/dao/vo/
- 模块间有依赖关系（如 dataapi 依赖 uic 认证）
- 每个模块的 conftest 不同

### 5. 复杂认证机制
- SM2 加密 + Cookie 认证
- `BaseCookies` 单例，通过 API 登录获取
- 自动在 `BaseRequests.__init__` 中调用
- 涉及多步认证流程（获取公钥 → 加密密码 → 登录 → 获取 cookie）

### 6. 测试数据管理
- 独立的 `testdata/` 目录，与 `testcases/` 同构
- 多种数据源的测试数据（MySQL、Oracle、Hive、Kafka、ES 等）
- DDL 驱动的数据初始化和清理

### 7. DAO 层 + 数据库验证
- `dao/` 目录包含 SQL 查询
- 每个环境配置不同的数据库连接
- L4 断言可用 DB 验证，但需要多环境数据库配置

### 8. 性能监控体系
- BaseRequests 有 `calc_request_time_and_alarm` 装饰器
- >3s 的请求触发钉钉告警
- InfluxDB 记录慢请求数据

### 9. 自定义 pytest 配置
- 6 个 markers: smoke, kerberos, tpcds, cdp, cdh
- 使用 pytest-ordering、pytest-rerunfailures
- 自定义结果统计（pytest_terminal_summary）

### 10. Allure 使用惯例
- `@allure.feature("离线开发")` 中文 feature 名
- 请求/响应通过 BaseRequests 自动 attach
- 特定模块使用特定 layer

### 11. 数据清理策略
- 通过 API 创建的数据用 yield fixture 清理
- 通过 SQL 创建的数据用 DDL 清理
- 有共享状态目录 `.pytest_shared/`

### 12. 依赖与环境
- Python 3.8（旧版本兼容）
- 40+ 第三方依赖（大量 DB 驱动）
- pip 包管理器 + requirements.txt

---

## 二、初始化流程重设计

### 当前 tide 的初始化路径

```
/using-tide
  → 分类检测（new / existing）
  → 项目扫描（project-scanner）
  → 交互确认（7 维度 + 仓库 + 连接）
  → 生成配置
```

问题：**只做了一维检测**。把 "Enum API"、"BaseRequests"、"cookie auth" 等当作独立标签，没有理解它们之间的关联。

### 改进后：分层递进式初始化

```
/using-tide
  |
  ├── 第 1 层：基础识别（~10 秒，自动）
  │   ├── 语言与框架检测（Python/pytest/Jest/...）
  │   ├── 项目分类（new / existing / enhanced）
  │   └── 复杂度评估（simple / moderate / complex）
  │
  ├── 第 2 层：深度扫描（根据复杂度分支）
  │   ├── simple → 快速扫描（当前实现）
  │   ├── moderate → 标准扫描 + 基础架构检测
  │   └── complex → 全面扫描（12 维度全开）
  │
  ├── 第 3 层：架构感知交互
  │   ├── 确认基础属性（已实现）
  │   ├── 多环境检测与配置（新增）
  │   ├── 运行方式确认（新增）
  │   └── 监控/告警体系确认（新增）
  │
  └── 第 4 层：生成配置
      ├── tide-config.yaml（扩展结构）
      ├── 多环境 env 映射
      ├── 自定义 runner 适配
      └── CLAUDE.md 增强
```

### 核心差异

| 维度 | 当前 | 改进后 |
|------|------|--------|
| 环境 | 单 Base URL | 检测 + 列出所有环境，用户选择默认/全配置 |
| 运行器 | 只输出 pytest 命令 | 检测自定义 runner，生成与其匹配的验收命令 |
| conftest | 不检测 | 解析 conftest fixture 链，记录可用 fixture |
| 模块关系 | 独立的模块列表 | 模块间依赖关系图 |
| 认证 | 知道 cookie/token | 检测认证步骤链（多步登录流程） |
| 数据管理 | 知道 separated/inline | 检测具体的数据源类型和清理策略 |
| 性能 | 不检测 | 检测自定义监控逻辑（告警、指标收集） |
| 测试配置 | 不检测 | 检测 markers（自动读取 pytest.ini）、插件列表 |
| 依赖 | 不检测 | 检测 Python 版本、包管理器、关键依赖版本 |

---

## 三、tide-config.yaml 扩展设计

```yaml
project:
  name: "dtstack-httprunner"
  type: existing
  complexity: complex          # simple | moderate | complex

# 环境（多环境支持）
environments:
  detected:
    - name: ci_52
      file: config/env/ci_52_insightci.ini
    - name: ci_62
      file: config/env/ci_62_insightci.ini
    - name: ci_63
      file: config/env/ci_63_insightci.ini
    - name: dm_63
      file: config/env/dm_63_mysql_env.ini
    - name: test_63_batch
      file: config/env/test_63_batch.ini
    - name: test_63_dm_batch
      file: config/env/test_63_dm_batch.ini
  active: "test_63_dm_batch"        # 当前 .env 指向的
  switch_method: "dotenv"           # dotenv | env_var | hardcode
  env_file: ".env"                  # 切换入口文件
  config_module: "config.env_config" # ENV_CONF 所在模块

# 代码规范（现有字段 + 扩展）
code_style:
  api_pattern:
    type: enum
    modules: 11                     # 11 个 Enum 模块
  http_client:
    type: custom_class
    class: "BaseRequests"
    module: "utils.common.BaseRequests"
    method_signature: "post(self, url, desc, **kwargs)"
    auth_injection: auto            # 构造时自动注入 cookie
  assertion:
    style: "resp['code'] == 1"
    helper_methods:
      - assert_status_code
      - assert_response_json
      - assert_response_success
    custom_assert: true
  test_structure:
    file_suffix: "*_test.py"
    fixture_style: setup_class
    class_pattern: "Test{Feature}"
    method_prefix: "test_"
    conftest_layers:
      - root: conftest.py
      - module: testcases/scenariotest/conftest.py
      - sub: testcases/scenariotest/{module}/conftest.py

# 测试运行配置
test_runner:
  type: custom                       # custom | pytest_direct
  entry: "run_demo.py"
  default_options:
    parallel: true
    workers: 8
    reruns: 1
    rerun_delay: 2
    report:
      - allure
      - json
  run_commands:
    batch: "python run_demo.py"
    dataapi: "python run_demo.py --module dataapi"
    stream: "python run_demo.py --module stream"

# 认证配置
auth:
  type: cookie
  class: "BaseCookies"
  module: "utils.common.get_cookies"
  flow:
    - get_public_key              # SM2 公钥获取
    - encrypt_password            # 密码加密
    - login                       # 登录获取 cookie
    - auto_renew: true            # 自动续期
  credentials_from: config.env_config  # 从 ENV_CONF 读取
  test_account:
    fields: ["username", "password", "tenant_name"]

# 监控与告警
monitoring:
  perf_alert:
    enabled: true
    threshold_ms: 3000
    channel: dingtalk
    metric_store: influxdb
    influx_config:
      url: "http://172.16.113.237:8086"
      org: "lc"
      bucket: "lc"

# 模块架构
modules:
  - name: batch
    api_enum: BatchApi
    test_dir: testcases/scenariotest/batch
    data_dir: testdata/scenariotest/batch
    dao_dir: dao/batch
    utils_dir: utils/batchv2
    conftest: testcases/scenariotest/batch/conftest.py
  - name: dataapi
    api_enum: DataAPIsApi
    test_dir: testcases/scenariotest/dataapi
    depends_on: [uic]               # 依赖关系
  # ...
```

---

## 四、实施建议

### Phase 2a：扫描增强（2-3 天）
- 新增 `detect_env_management` — 检测多环境模式
- 新增 `detect_test_runner` — 检测自定义 runner
- 新增 `detect_conftest_chain` — 解析 conftest 链
- 新增 `detect_auth_flow` — 检测认证步骤
- 新增 `detect_monitoring` — 检测监控/告警体系
- 新增 `detect_module_deps` — 检测模块间依赖

### Phase 2b：配置扩展（1-2 天）
- `tide-config.yaml` schema 扩展（多环境/自定义 runner/模块架构）
- `/using-tide` 交互式向导增加相应环节
- 配置文件版本兼容

### Phase 2c：生成适配（2-3 天）
- 新增 `50-env-config.md` — 环境配置 prompt 模块
- 新增 `60-custom-runner.md` — 自定义运行器 prompt 模块
- 新增 `70-auth-flow.md` — 认证流程 prompt 模块
- case-writer 根据深度配置生成精准匹配的代码
