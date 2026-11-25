---
name: mra-sync
description: Use when the delta specs of an in-progress OpenSpec change in an mra-flow orchestrator must reach the main specs before archive, e.g. so another change can build on them - in the mra-flow workflow.
disable-model-invocation: true
argument-hint: <change-id>
---

# mra-sync — sync delta specs to main specs

Merge the change's delta specs into `openspec/specs/` without archiving it. `/mra-archive` does this anyway; use `/mra-sync` only when the main specs are needed earlier.

## Steps

1. `openspec validate <change-id> --strict` passes. Stop if not.
2. Tell the user that synced specs describe behavior that may not be built yet (check `bd epic status` for the change's epic), and confirm before going on.
3. Call the Skill tool with `openspec-sync-specs` for `<change-id>` and follow it.
4. Run `openspec validate --specs --strict` and report the result.
5. Note it on the epic, if one exists: `bd update <epic> --append-notes "specs synced <date>"`.

## Rules

- Show the model at work: `Model: <model> (<role>)` at the phase start, with every subagent dispatch and whenever it changes; see `.mra-flow/docs/agents/model-display.md`.
- Do not tick `tasks.md`, close beads issues, or archive here.
