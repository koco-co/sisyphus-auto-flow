# targeted-executor

## Purpose

Consume the **workflow manifest** and run only the impacted tests needed for this HAR iteration.

## Required inputs

- `.data/parsed/<name>.workflow.json`
- resolved targeted test paths
- generated code under `api/`, `tests/`, and `testdata/`

## Must do

- run only the module/file targets named by the workflow manifest
- capture execution output for the main agent
- prepare data needed by the terminal acceptance checklist

## Must not do

- do not trigger a full business regression run
- do not generate a tracked acceptance file
- do not pull in `CustomItem`

