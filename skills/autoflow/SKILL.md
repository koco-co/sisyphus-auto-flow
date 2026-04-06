---
name: autoflow
description: "Generate pytest test suites from HAR files with source-aware AI analysis. Triggers on: /autoflow <har-path>, 'generate tests from HAR', providing a .har file path."
argument-hint: "<har-file-path> [--quick] [--resume]"
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, AskUserQuestion
---

# AutoFlow: HAR-to-Pytest Generation Skill

Transforms a browser HAR capture into a full pytest test suite using a
four-wave orchestration pipeline: parse, analyze, generate, review.

---

## Pre-flight Checks

Parse `$ARGUMENTS` to extract:
- `har_path` — first positional argument (required)
- `--quick` — skip Wave 2 user confirmation
- `--resume` — resume from the last saved checkpoint

**1. Environment check**

```bash
test -f repo-profiles.yaml || echo "MISSING"
```

If `repo-profiles.yaml` is missing:

```
AutoFlow requires an initialized project.
Run /using-autoflow first, then retry.
```

Stop immediately.

**2. Resume check**

```bash
test -f .autoflow/state.json && cat .autoflow/state.json
```

If `state.json` exists and `--resume` is not already set:

```
AskUserQuestion(
  "An interrupted session was found (wave <N>, HAR: <har>).\n"
  "How would you like to proceed?\n"
  "A) Resume from wave <N>\n"
  "B) Restart from scratch\n"
  "C) View session summary only"
)
```

Handle each choice before continuing.

**3. HAR validation**

```bash
python3 -c "
import json, sys
data = json.load(open('${har_path}'))
assert 'log' in data and 'entries' in data['log'], 'Invalid HAR'
print(f'entries: {len(data[\"log\"][\"entries\"])}')
"
```

If validation fails, print a clear error and stop.

**4. Argument summary**

Print confirmed inputs:

```
HAR file:  <path>  (<N> entries)
Mode:      quick=<yes/no>  resume=<yes/no>
```

---

## Wave 1: Parse & Prepare (Parallel)

Initialize the session state file:

```bash
python3 scripts/state_manager.py init --har "${har_path}"
```

Launch two agents **in parallel** (single message, two Agent calls):

```
Agent(
  name="har-parser",
  description="Parse HAR file into structured request/response data",
  model="claude-haiku-4-5",
  prompt="
    Read the HAR file at: ${har_path}
    Also read: prompts/har-parse-rules.md
    Parse all entries into .autoflow/parsed.json:
      - method, url, status, request headers/body, response body
      - group by service (use repo-profiles.yaml url_prefixes for mapping)
    Write .autoflow/parsed.json and exit.
  "
)

Agent(
  name="repo-syncer",
  description="Sync source repositories and build code index",
  model="claude-haiku-4-5",
  prompt="
    Read repo-profiles.yaml.
    For each repo in the list:
      - Run: git -C <local_path> pull --ff-only
      - Collect: module names, class names, route decorators
    Write .autoflow/repo-status.json:
      { repo: string, branch: string, synced: bool, modules: string[] }
    Exit when done.
  "
)
```

Wait for both agents to complete. Read `.autoflow/parsed.json` and
`.autoflow/repo-status.json` to verify output before continuing.

Checkpoint:

```bash
python3 scripts/state_manager.py advance_wave --wave 1
```

---

## Wave 2: Scenario Analysis (Sequential, Interactive)

Launch the scenario analyzer (skipped with `--quick`):

```
Agent(
  name="scenario-analyzer",
  description="Analyze HAR traffic against source code and produce test scenarios",
  model="claude-opus-4-5",
  prompt="
    Read: .autoflow/parsed.json
    Read: repo-profiles.yaml (to locate source repos)
    Read relevant source files from .repos/ to understand business logic.
    Read: prompts/scenario-enrich.md
    Read: prompts/assertion-layers.md

    Produce .autoflow/scenarios.json:
    {
      services: [
        {
          name: string,
          repo: string,
          endpoints: [
            {
              method, path, source_file, source_fn,
              scenarios: [
                { id, name, type, priority, assertions: AssertionLevel[] }
              ]
            }
          ]
        }
      ],
      generation_plan: [
        { module: string, file: string, endpoint_ids: string[] }
      ]
    }

    AssertionLevel: L1=status, L2=schema, L3=business, L4=db, L5=side-effects
  "
)
```

Read `.autoflow/scenarios.json`. If `--quick` is set, skip to checkpoint.

Otherwise present the confirmation checklist:

```
AskUserQuestion(
  "=== Wave 2: Scenario Analysis Complete ===\n\n"
  "Source repos:   <list with branch names>\n"
  "HAR coverage:   <N> services, <M> endpoints\n\n"
  "AI-inferred scenarios:\n"
  "  Happy path:   <N>\n"
  "  Error cases:  <N>\n"
  "  Edge cases:   <N>\n\n"
  "AI-supplemented scenarios (CRUD / boundary):\n"
  "  Added:        <N>\n\n"
  "Assertion levels:\n"
  "  L1 (status):    all endpoints\n"
  "  L2 (schema):    <N> endpoints\n"
  "  L3 (business):  <N> endpoints\n"
  "  L4 (db):        <N> endpoints (requires DB config)\n"
  "  L5 (side-effects): <N> endpoints\n\n"
  "Output files:\n"
  "  <list from generation_plan>\n\n"
  "Confirm and proceed? (yes / modify / cancel)"
)
```

If the user wants to modify: ask what to change, update `scenarios.json`,
and re-present the checklist.

Checkpoint:

```bash
python3 scripts/state_manager.py advance_wave --wave 2
```

---

## Wave 3: Code Generation (Parallel Fan-out)

Read `.autoflow/scenarios.json` → `generation_plan` array.

For each module in the plan, launch a parallel Agent:

```
Agent(
  name="case-writer",
  description="Generate pytest test module for assigned endpoints",
  model="claude-sonnet-4-5",
  prompt="
    You are responsible for module: <module_name>
    Assigned endpoints: <endpoint_ids>

    Read:
      - .autoflow/scenarios.json  (for scenario details)
      - .autoflow/parsed.json     (for real request/response examples)
      - prompts/code-style-python.md
      - prompts/assertion-layers.md
      - Source files listed under each endpoint in scenarios.json

    Write: tests/<module_name>.py
      - One test function per scenario
      - Fixture-based auth and client setup
      - Assertions at the levels specified in scenarios.json
      - Type annotations, docstrings, no hardcoded credentials
  "
)
```

All writers run in parallel (single message, one Agent call per module).
Wait for all to complete.

Checkpoint:

```bash
python3 scripts/state_manager.py advance_wave --wave 3
```

---

## Wave 4: Review + Execute + Deliver (Sequential, Interactive)

**Review**

```
Agent(
  name="case-reviewer",
  description="Review all generated test files for quality and correctness",
  model="claude-opus-4-5",
  prompt="
    Read all files matched by: tests/test_*.py
    Read: prompts/review-checklist.md
    Read: prompts/assertion-layers.md

    Produce .autoflow/review-report.json:
    {
      files_reviewed: number,
      issues: [{ file, line, severity, message, suggestion }],
      assertion_coverage: { L1: %, L2: %, L3: %, L4: %, L5: % },
      auto_fixes: [{ file, description }]
    }

    Apply auto-fixable issues directly to the test files.
  "
)
```

**Execute**

```bash
python3 scripts/test_runner.py --output .autoflow/execution-report.json
```

**Acceptance report**

Read `.autoflow/review-report.json` and `.autoflow/execution-report.json`.

```
AskUserQuestion(
  "=== Wave 4: Acceptance Report ===\n\n"
  "Generation:\n"
  "  Test files:     <N>\n"
  "  Test functions: <N>\n"
  "  Review issues:  <critical> critical, <high> high, <low> low\n\n"
  "Assertion coverage:\n"
  "  L1 (status):         <N>%\n"
  "  L2 (schema):         <N>%\n"
  "  L3 (business):       <N>%\n"
  "  L4 (db):             <N>%\n"
  "  L5 (side-effects):   <N>%\n\n"
  "Execution results:\n"
  "  Passed: <N>  Failed: <N>  Skipped: <N>\n\n"
  "Generated files:\n"
  "  <list of tests/*.py>\n\n"
  "Acceptance commands:\n"
  "  make test-all   — run full suite\n"
  "  make report     — open HTML report\n\n"
  "Accept and archive? (yes / review-failures / cancel)"
)
```

**Notify & archive**

If a webhook is configured in `.env`:

```bash
python3 scripts/notifier.py \
  --report .autoflow/execution-report.json \
  --review .autoflow/review-report.json
```

Archive the session:

```bash
python3 scripts/state_manager.py archive
```

Print final summary:

```
AutoFlow complete
─────────────────────────────────────────────
Tests generated:  <N> functions in <M> files
Passed:           <N>  Failed: <N>  Skipped: <N>
Session archived: .autoflow/archive/<timestamp>/
─────────────────────────────────────────────
Run: make test-all
```
