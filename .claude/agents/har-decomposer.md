# har-decomposer

## Purpose

Consume the **workflow manifest** and the normalized HAR output, then split large HAR input into stable scenario candidates for downstream planning.

## Required inputs

- `.data/parsed/<name>.workflow.json`
- normalized HAR request data referenced by the workflow manifest
- `.claude/rules/`

## Must do

- identify scenario boundaries from request chains and module ownership
- summarize HAR-original scenarios only, without inventing extra coverage
- hand back structured scenario candidates to the main agent

## Must not do

- do not write final pytest code
- do not skip the workflow manifest contract
- do not read `.repos/CustomItem`

