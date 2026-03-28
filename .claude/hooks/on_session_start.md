# 会话启动钩子

Agent 每次启动新会话时，自动执行以下操作：

## 1. 清理过期文件

```bash
bash .claude/scripts/cleanup_trash.sh
```

清理 `.trash/` 和 `.data/parsed/` 中超过 7 天的过期文件。

## 2. 检查待处理 HAR 文件

检查 `.data/har/` 目录是否存在待处理的 HAR 文件。如果有，提示用户是否开始 HAR → 测试用例的转化工作流。

## 3. 阅读项目规范

在生成任何代码之前，确保已阅读以下规范：

- `.claude/rules/CONVENTIONS.md` — 命名与代码风格
- `.claude/rules/ASSERTIONS.md` — 断言使用规范
- `.claude/rules/PATTERNS.md` — 测试场景模式
- `.claude/rules/DATABASE.md` — 数据库断言模式
- `.claude/rules/COMMITS.md` — 代码提交规范
