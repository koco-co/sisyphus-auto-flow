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

cd "$repo_root"
uv run python -m sisyphus_auto_flow.parsers.har_parser "$har_file" --output "$output_path"
