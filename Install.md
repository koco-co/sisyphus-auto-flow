# Install

## macOS

1. 安装 Python 3.13+
2. 安装 `uv`
3. 克隆仓库并进入项目目录
4. 执行 `make install`
5. 执行 `make test` 验证环境

```bash
brew install uv
git clone https://github.com/koco-co/sisyphus-auto-flow.git
cd sisyphus-auto-flow
make install
make test
```

## Windows

1. 安装 Python 3.13+
2. 安装 `uv`
3. 使用 PowerShell 克隆仓库并进入目录
4. 执行 `make install`
5. 执行 `make test` 验证环境

```powershell
winget install astral-sh.uv
git clone https://github.com/koco-co/sisyphus-auto-flow.git
cd sisyphus-auto-flow
make install
make test
```

## AI / Agent 使用前准备

1. 确认 `.repos/`、`.data/parsed/`、`.trash/` 目录存在
2. 如需参考后端源码，先执行：

```bash
.claude/scripts/sync_release_repos.sh release_6.2.x
```

3. 如果要走完整 AI 工作流，可先阅读：
   - `README.md`
   - `CLAUDE.md`
   - `.claude/skills/using-autoflow/SKILL.md`

## 验证安装成功

```bash
make type-check
make lint
make test
```
