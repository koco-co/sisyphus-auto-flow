#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: .claude/scripts/render_acceptance_summary.sh <workflow_manifest_json>" >&2
  exit 1
fi

uv run saf render-acceptance --manifest "$1"
