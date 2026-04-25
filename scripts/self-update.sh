#!/usr/bin/env bash
# Tide 自更新脚本 — 在 /using-tide 和 /tide 启动时自动检查并更新插件代码。
set -euo pipefail

REPO_URL="https://github.com/koco-co/tide.git"
CHECK_INTERVAL=86400  # 24 小时

# 查找 Tide 插件安装路径
find_plugin_path() {
    local config="$HOME/.claude/plugins/installed_plugins.json"
    [ -f "$config" ] || return 1
    python3 -c "
import json
with open('$config') as f:
    data = json.load(f)
for entries in data.get('plugins', {}).values():
    for e in entries:
        if 'tide' in e.get('installPath', ''):
            print(e['installPath'])
            exit(0)
exit(1)
" 2>/dev/null || return 1
}

# 读取 installed_plugins.json 中记录的 commit SHA
get_installed_sha() {
    local config="$HOME/.claude/plugins/installed_plugins.json"
    [ -f "$config" ] || return 1
    python3 -c "
import json
with open('$config') as f:
    data = json.load(f)
for entries in data.get('plugins', {}).values():
    for e in entries:
        if e.get('installPath') == '$1':
            print(e.get('gitCommitSha', ''))
            exit(0)
exit(1)
" 2>/dev/null || true
}

# 检查是否超过检查间隔
should_check() {
    local state_file="$1/.tide/self-update-state.json"
    [ -f "$state_file" ] || return 0
    local last_check
    last_check=$(python3 -c "
import json
with open('$state_file') as f:
    print(json.load(f).get('last_check', 0))
" 2>/dev/null || echo "0")
    local now
    now=$(date +%s)
    [ $((now - last_check)) -gt $CHECK_INTERVAL ]
}

# 记录本次检查时间
save_check_time() {
    local dir="$1/.tide"
    mkdir -p "$dir"
    printf '{"last_check":%d}\n' "$(date +%s)" > "$dir/self-update-state.json"
}

# 更新 installed_plugins.json 中的 SHA
update_sha() {
    local plugin_path="$1" new_sha="$2"
    local config="$HOME/.claude/plugins/installed_plugins.json"
    [ -f "$config" ] || return 1
    python3 -c "
import json, time
with open('$config') as f:
    data = json.load(f)
for entries in data.get('plugins', {}).values():
    for e in entries:
        if e.get('installPath') == '$plugin_path':
            e['gitCommitSha'] = '$new_sha'
            e['lastUpdated'] = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
with open('$config', 'w') as f:
    json.dump(data, f, indent=2)
" 2>/dev/null
}

# 主流程
main() {
    local plugin_path
    plugin_path=$(find_plugin_path) || return 0
    [ -n "$plugin_path" ] || return 0

    # 检查间隔
    should_check "$plugin_path" || return 0

    # 记录本次检查
    save_check_time "$plugin_path"

    # 查询远程最新 SHA
    local remote_sha
    remote_sha=$(git ls-remote "$REPO_URL" main 2>/dev/null | awk '{print $1}')
    [ -n "$remote_sha" ] || return 0

    # 与本地 SHA 对比
    local installed_sha
    installed_sha=$(get_installed_sha "$plugin_path")
    [ "$installed_sha" != "$remote_sha" ] || return 0

    # 有更新，拉取代码
    local tmp_dir
    tmp_dir=$(mktemp -d "/tmp/tide-update-XXXXXX")
    # shellcheck disable=SC2064
    trap "rm -rf '$tmp_dir'" EXIT

    git clone --depth 1 -b main "$REPO_URL" "$tmp_dir/tide" 2>/dev/null || return 0
    [ -d "$tmp_dir/tide" ] || return 0

    rsync -a --delete \
        --exclude=.venv --exclude=.git --exclude=.worktrees \
        --exclude=.tide --exclude=__pycache__ --exclude='*.pyc' \
        --exclude=.pytest_cache --exclude=.DS_Store \
        "$tmp_dir/tide/" "$plugin_path/" 2>/dev/null || return 0

    update_sha "$plugin_path" "$remote_sha"
    echo "[tide] 插件已自动更新到最新版本"
}

main "$@"
