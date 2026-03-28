#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "Usage: $0 <har_file> [output_path]" >&2
  exit 1
fi

script_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
repo_root="$(cd -- "$script_dir/../.." && pwd)"

har_file="$1"
output_path="${2:-$repo_root/.data/parsed/parsed_requests.json}"
working_har="$har_file"

if ! python - "$har_file" "$repo_root" <<'PY'
from pathlib import Path
import sys

har_path = Path(sys.argv[1]).resolve()
repo_root = Path(sys.argv[2]).resolve()
try:
    har_path.relative_to(repo_root)
except ValueError:
    raise SystemExit(1)
PY
then
  mkdir -p "$repo_root/.data/har"
  working_har="$repo_root/.data/har/$(basename "$har_file")"
  cp "$har_file" "$working_har"
fi

cd "$repo_root"
uv run python -m sisyphus_auto_flow.parsers.har_parser "$working_har" --output "$output_path"
