#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 3 ]; then
  echo "Usage: .claude/scripts/plan_har_workflow.sh <har_file> <release> <output_json>" >&2
  exit 1
fi

HAR_FILE="$1"
RELEASE="$2"
OUTPUT_JSON="$3"

uv run saf plan-har --har "${HAR_FILE}" --release "${RELEASE}" --output "${OUTPUT_JSON}"
