---
name: HAR 转测试用例
description: 将 Chrome HAR 文件转换为标准化的 pytest API 测试用例
triggers:
  - har
  - 测试用例
  - 接口测试
  - 自动化测试
  - 生成用例
---

# HAR → 测试用例生成 Skill

## 概述

本 Skill 实现从 Chrome HAR 文件到标准化 pytest API 测试用例的完整转换工作流。
结合源码分析和交互式确认，生成高质量、风格统一的接口自动化测试代码。

## 工作流程

### 第一步：解析 HAR 文件
```bash
python -m sisyphus_auto_flow.scripts.parse_har <har文件路径> --output tmp/parsed_requests.json
```
- 自动过滤静态资源（CSS、JS、图片等）
- 识别请求链和上下文关系
- 解析后自动将 HAR 文件移入 `.trash/` 目录

### 第二步：分析源码
浏览 `.repos/` 目录下的服务源码：
- 找到对应的接口 handler、路由定义
- 理解请求/响应模型（DTO）
- 了解数据库模型和业务逻辑
- 识别校验规则和错误处理

### 第三步：交互式场景确认
向用户展示以下内容供确认：
1. **已识别的接口列表**（从 HAR 中提取）
2. **建议补充的场景**（CRUD 闭环、异常覆盖、权限校验）
3. **断言计划**（状态码、响应体、数据库、性能）
4. **数据库断言方案**（pre_sql 清理、post_sql 验证）

### 第四步：生成测试代码
- 使用 Jinja2 模板或直接生成
- 所有代码遵守 `rules/CONVENTIONS.md` 规范
- 所有断言遵守 `rules/ASSERTIONS.md` 规范
- 所有场景遵守 `rules/PATTERNS.md` 模式

### 第五步：执行与自动修复
```bash
uv run pytest tests/<模块>/ -v --alluredir=allure-results
```
- 如果测试失败，分析错误原因并自动修复
- 循环执行直到所有用例通过

### 第六步：报告与通知
- 生成 Allure 报告
- 通知用户查看和验收

## 可用模板

| 模板文件 | 用途 | 适用场景 |
|---------|------|---------|
| `crud_scenario.py.j2` | CRUD 生命周期 | 增改查删完整场景 |
| `auth_scenario.py.j2` | 认证场景 | 登录、token、权限 |
| `negative_scenario.py.j2` | 异常场景 | 参数错误、404、409 |

## 依赖的规则文件

- `rules/CONVENTIONS.md` — 代码规范（命名、结构、风格）
- `rules/ASSERTIONS.md` — 断言规范（优先级、使用方式）
- `rules/PATTERNS.md` — 场景模式（CRUD、认证、异常）
- `rules/DATABASE.md` — 数据库断言规范
- `rules/EXAMPLES.md` — 完整参考示例

## 关键约束

1. 所有测试类继承 `BaseAPITest`
2. 所有注释和文档使用中文
3. 测试数据使用 `autotest_` 前缀
4. 严格遵守 Arrange-Act-Assert 模式
5. 断言优先级：状态码 → 结构 → 值 → 数据库 → 性能
