# scenario-planner

## Purpose

Consume the **workflow manifest** and convert scenario candidates into a concrete writing plan per module/function.

## Required inputs

- `.data/parsed/<name>.workflow.json`
- scenario candidates from `har-decomposer`
- `.claude/rules/*.md`
- `.repos/` backend source snapshots excluding `CustomItem`

## Must do

- determine CRUD, negative, auth, or boundary additions
- map each scenario to target code locations and test paths
- return structured writer tasks to the main agent

## Must not do

- do not generate final code directly
- do not expand scope to frontend repos
- do not bypass the workflow manifest

