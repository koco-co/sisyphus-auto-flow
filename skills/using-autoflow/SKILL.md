---
name: using-autoflow
description: "初始化 AutoFlow 环境 — 项目脚手架、仓库配置、技术栈设置。适用场景：首次运行、/using-autoflow、'初始化 autoflow'、'设置 autoflow'。"
argument-hint: "[--force]"
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
---

# AutoFlow 初始化技能

为新项目或已有项目引导安装 AutoFlow 自动化测试框架。
流程包括：环境校验、技术栈选择、仓库接入、连接配置，
最终生成项目脚手架和 CLAUDE.md。

---

## 第一步：环境检测

检查所有必要工具是否可用，并输出各工具的状态。

```bash
python3 --version   # 要求 >= 3.12
uv --version        # 要求 uv 包管理器
git --version       # 要求 git
```

同时检测当前是否为已有项目：

```bash
test -f pyproject.toml && echo "existing" || echo "new"
```

输出状态表格：

| 工具      | 要求版本 | 检测版本 | 状态 |
|-----------|----------|----------|------|
| Python    | >= 3.12  | x.y.z    | 正常/失败 |
| uv        | 任意     | x.y.z    | 正常/失败 |
| git       | 任意     | x.y.z    | 正常/失败 |
| pyproject | —        | 是/否    | 信息 |

若有必要工具缺失，打印安装说明并终止。

---

## 第二步：项目风格检测与确认

### 已有项目

扫描项目中已有的风格配置：

- 读取 `pyproject.toml` 中的 `[tool.ruff]`、`[tool.mypy]`、`[tool.pyright]`
- 若存在，读取 `.editorconfig`
- 若存在，读取 `ruff.toml`
- 读取 `tests/` 下测试文件头部，推断编码规范

然后询问：

```
AskUserQuestion(
  "检测到已有配置，请选择处理方式：\n"
  "A) 保留现有风格（推荐）\n"
  "B) 覆盖为 AutoFlow 默认配置\n"
  "C) 手动自定义"
)
```

### 新项目

请用户选择技术栈：

```
AskUserQuestion(
  "请为本项目选择技术栈：\n"
  "A) 推荐：Python 3.13 + uv + ruff + pyright + pre-commit + rich + make\n"
  "B) 保守：Python 3.12 + pip + flake8 + mypy + pytest-html\n"
  "C) 自定义：请输入您的偏好"
)
```

若用户选择 C，逐项询问：
- Python 版本
- 包管理器（uv / pip / poetry）
- 代码检查工具（ruff / flake8 / pylint）
- 类型检查工具（pyright / mypy）
- 可选扩展（pre-commit、rich、make）

将确认后的技术栈存储为 `_stack`，供后续步骤使用。

---

## 第三步：源码仓库配置

询问一个或多个待克隆的源码仓库 URL：

```
AskUserQuestion(
  "请输入源码仓库 URL（每行一个，可附加 @branch 后缀）：\n"
  "示例：\n"
  "  https://git.example.com/group1/backend.git\n"
  "  https://git.example.com/group2/api.git@develop\n"
  "输入完毕后留空回车。"
)
```

根据 URL 自动推导本地路径：

```
https://git.example.com/group1/repo1.git  →  .repos/group1/repo1/
https://git.example.com/group2/repo2.git@develop  →  .repos/group2/repo2/（分支：develop）
```

克隆并切换每个仓库：

```bash
git clone <url> <local_path>
git -C <local_path> checkout <branch>   # 若指定了分支
```

然后询问 URL 前缀与仓库的映射关系，供 HAR 分析器定位请求所属仓库：

```
AskUserQuestion(
  "请配置 URL 前缀与仓库的映射（每行一条）：\n"
  "格式：<url-prefix> → <repo-name>\n"
  "示例：\n"
  "  /api/v1 → backend\n"
  "  /admin  → admin-portal\n"
  "输入完毕后留空回车。"
)
```

在项目根目录生成 `repo-profiles.yaml`：

```yaml
# repo-profiles.yaml — 由 /using-autoflow 自动生成
repos:
  - name: <repo-name>
    local_path: .repos/<group>/<repo>/
    remote: <url>
    branch: <branch>
    url_prefixes:
      - <prefix1>
      - <prefix2>
```

---

## 第四步：连接配置

询问被测系统的 Base URL：

```
AskUserQuestion(
  "请输入目标系统的 Base URL（例如：http://172.16.115.247）："
)
```

询问认证方式：

```
AskUserQuestion(
  "请选择认证方式：\n"
  "A) Cookie（粘贴原始 Cookie 请求头值）\n"
  "B) Token（Bearer token）\n"
  "C) 用户名 + 密码"
)
```

根据所选方式逐项收集凭证（每个字段单独一次 AskUserQuestion）。

询问可选集成项：

```
AskUserQuestion(
  "是否配置数据库连接？（y/n）\n"
  "如选是，将依次询问主机、端口、用户名、密码及数据库名。"
)
```

若选是，逐项收集数据库字段。

```
AskUserQuestion(
  "是否配置通知 Webhook？（y/n）\n"
  "支持：钉钉、飞书、Slack"
)
```

若选是，询问 Webhook URL 和平台类型。

写入 `.env` 和 `.env.example`：

`.env` — 包含真实值（已加入 .gitignore）：
```
BASE_URL=<value>
AUTH_COOKIE=<value>        # 或 AUTH_TOKEN / AUTH_USER + AUTH_PASS
DB_HOST=<value>            # 若已配置数据库
NOTIFY_WEBHOOK=<value>     # 若已配置通知
NOTIFY_PLATFORM=<value>    # dingtalk | feishu | slack
```

`.env.example` — 仅含占位符（提交至版本控制）：
```
BASE_URL=http://your-server
AUTH_COOKIE=your_cookie_here
```

---

## 第五步：脚手架生成 + CLAUDE.md

运行脚手架脚本，生成项目目录结构：

```bash
python3 ${CLAUDE_SKILL_DIR}/../../scripts/scaffold.py \
  --stack "${_stack}" \
  --base-url "${BASE_URL}"
```

脚本将创建以下文件：
```
tests/
  conftest.py
  test_smoke.py
Makefile          （若技术栈包含 make）
pyproject.toml    （已更新）
.pre-commit-config.yaml  （若技术栈包含 pre-commit）
.gitignore        （确保 .env、.repos/ 已被忽略）
```

在项目根目录自动生成 `CLAUDE.md`，包含以下章节：

```markdown
# CLAUDE.md — AutoFlow 项目

## 技术栈
<第二步确认的技术栈>

## 项目结构
<目录树>

## 源码仓库引用
<repo-profiles.yaml 中的仓库列表及本地路径>

## 规范索引
- 测试目录：tests/
- Fixture：tests/conftest.py
- 断言规范：见 prompts/assertion-layers.md
- 代码风格：见 prompts/code-style-python.md

## 环境信息
- Base URL：${BASE_URL}
- 认证方式：<method>
- 数据库：<已配置 / 未配置>
- 通知：<已配置 / 未配置>
```

最后打印初始化摘要：

```
AutoFlow 初始化完成
──────────────────────────────────────────
技术栈：      Python 3.13 + uv + ruff + pyright
已克隆仓库：  2 个
URL 映射：    3 条
认证方式：    Cookie
数据库：      已配置
Webhook：     飞书
──────────────────────────────────────────
下一步：执行 /autoflow <path-to.har>
```
