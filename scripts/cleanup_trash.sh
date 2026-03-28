#!/usr/bin/env bash
# 回收站自动清理脚本
# 删除 .trash/ 目录下超过 7 天的文件
# 用法: bash scripts/cleanup_trash.sh
# 建议配置 crontab 定时执行: 0 2 * * * cd /path/to/project && bash scripts/cleanup_trash.sh

set -euo pipefail

TRASH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.trash"
RETENTION_DAYS=7

if [ ! -d "$TRASH_DIR" ]; then
    echo "回收站目录不存在: $TRASH_DIR"
    exit 0
fi

# 统计待清理文件
count=$(find "$TRASH_DIR" -type f -not -name ".gitkeep" -mtime +"$RETENTION_DAYS" | wc -l | tr -d ' ')

if [ "$count" -eq 0 ]; then
    echo "回收站无需清理（无超过 ${RETENTION_DAYS} 天的文件）"
    exit 0
fi

echo "正在清理 ${count} 个超过 ${RETENTION_DAYS} 天的文件..."

# 删除过期文件
find "$TRASH_DIR" -type f -not -name ".gitkeep" -mtime +"$RETENTION_DAYS" -print -delete

# 清理空目录
find "$TRASH_DIR" -type d -empty -not -path "$TRASH_DIR" -print -delete 2>/dev/null || true

echo "清理完成"
