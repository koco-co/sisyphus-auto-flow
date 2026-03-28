# test-writer

## Purpose

Consume one writer task from the **workflow manifest** and generate pytest code that matches project rules and templates.

## Required inputs

- `.data/parsed/<name>.workflow.json`
- one writer task assigned by the main agent
- `.claude/rules/*.md`
- `.repos/` backend source snapshots
- packaged templates plus `.claude/skills/har-to-testcase/references/`

## Must do

- keep naming, comments, and assertions aligned with project conventions
- generate only the assigned module/scenario scope
- update `api/`, `tests/`, and `testdata/` consistently when needed

## Must not do

- do not touch unrelated modules
- do not invent unsupported endpoints
- do not read or depend on `CustomItem`

