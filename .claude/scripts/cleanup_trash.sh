#!/usr/bin/env bash
# 回收站 + 数据暂存自动清理脚本
# Claude Code 会话启动时触发，清理超过 7 天的文件
# 用法: bash .claude/scripts/cleanup_trash.sh

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RETENTION_DAYS=7

# 清理 .trash/
TRASH_DIR="$PROJECT_ROOT/.trash"
if [ -d "$TRASH_DIR" ]; then
    count=$(find "$TRASH_DIR" -type f -not -name ".gitkeep" -mtime +"$RETENTION_DAYS" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$count" -gt 0 ]; then
        find "$TRASH_DIR" -type f -not -name ".gitkeep" -mtime +"$RETENTION_DAYS" -delete 2>/dev/null
        find "$TRASH_DIR" -type d -empty -not -path "$TRASH_DIR" -delete 2>/dev/null || true
        echo "✅ .trash/ 已清理 ${count} 个过期文件"
    fi
fi

# 清理 .data/parsed/
PARSED_DIR="$PROJECT_ROOT/.data/parsed"
if [ -d "$PARSED_DIR" ]; then
    count=$(find "$PARSED_DIR" -type f -not -name ".gitkeep" -mtime +"$RETENTION_DAYS" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$count" -gt 0 ]; then
        find "$PARSED_DIR" -type f -not -name ".gitkeep" -mtime +"$RETENTION_DAYS" -delete 2>/dev/null
        echo "✅ .data/parsed/ 已清理 ${count} 个过期文件"
    fi
fi
