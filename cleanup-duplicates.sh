#!/usr/bin/env bash
# cleanup-duplicates.sh — 检测并删除 macOS/iCloud 复制产生的 "xxx 2.yyy" 文件/目录
# 匹配模式: 名称中包含 " 2." 或以 " 2" 结尾（无扩展名的目录）

set -euo pipefail

ROOT="${1:-.}"

# 收集匹配项（排除 node_modules、.git）
mapfile -t items < <(
  find "$ROOT" \
    -name "node_modules" -prune -o \
    -name ".git" -prune -o \
    \( -name "* 2.*" -o -name "* 2" \) -print
)

if [[ ${#items[@]} -eq 0 ]]; then
  exit 0
fi

echo "🧹 清理 ${#items[@]} 个重复项:"
for item in "${items[@]}"; do
  rm -rf "$item"
  echo "  已删除: $item"
done
echo ""
