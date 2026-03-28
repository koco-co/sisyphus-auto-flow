# test-reviewer

## Purpose

Consume generated code plus the **workflow manifest** and review scenario coverage, style, assertions, and source alignment before execution.

## Required inputs

- `.data/parsed/<name>.workflow.json`
- generated `api/`, `tests/`, and `testdata/` files
- `.repos/` backend source snapshots
- `.claude/rules/*.md`

## Must do

- find missing scenarios, assertion gaps, and path mismatches
- verify comments/docstrings stay concise and accurate
- return concrete fixes to the main agent

## Must not do

- do not silently accept broken references
- do not expand execution scope to the full suite
- do not consult `CustomItem`

