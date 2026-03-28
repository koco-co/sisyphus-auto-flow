#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 3 ]; then
  echo "Usage: .claude/scripts/plan_har_workflow.sh <parsed_json_or_har_file> <release> <output_json>" >&2
  exit 1
fi

WORKFLOW_INPUT="$1"
RELEASE="$2"
OUTPUT_JSON="$3"

uv run saf plan-har --har "${WORKFLOW_INPUT}" --release "${RELEASE}" --output "${OUTPUT_JSON}"
