#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <scenario_json> <output_dir>" >&2
  exit 1
fi

script_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
repo_root="$(cd -- "$script_dir/../.." && pwd)"

scenario_json="$1"
output_dir="$2"

cd "$repo_root"
uv run python - "$scenario_json" "$output_dir" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

from sisyphus_auto_flow.core.models.test_case import TestScenario
from sisyphus_auto_flow.generator import CodeGenerator

scenario_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])
scenario = TestScenario.model_validate(
    json.loads(scenario_path.read_text(encoding="utf-8"))
)

generated = CodeGenerator().generate(scenario, output_path)
print(generated)
PY
