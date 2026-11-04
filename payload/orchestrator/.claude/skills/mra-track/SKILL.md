---
name: mra-track
description: Use when an OpenSpec change in an mra-flow orchestrator has validated artifacts and its tasks must be tracked in beads - phase 3 of the mra-flow workflow.
disable-model-invocation: true
argument-hint: <change-id>
---

# mra-track — phase 3: tasks.md → beads

Turn `openspec/changes/<change-id>/tasks.md` into a beads epic with one child issue per task. Conventions: `.mra-flow/docs/agents/issue-tracker.md`.

## Steps

1. Preconditions: `openspec validate <change-id> --strict` passes. Stop and report if not.
2. **Idempotency.** `bd list -t epic -l openspec:<change-id> --all --json`. If an epic exists, list its children (`bd children <epic>`) and only create what is missing; never duplicate.
3. Create the epic:
   ```bash
   bd create "<change-id>: <proposal title>" -t epic -l openspec:<change-id> \
     --spec-id openspec/changes/<change-id> -d "<proposal Why, 1-3 lines>" --silent
   ```
4. For each checkbox task `X.Y [<key>] <text>`, create a child (labels `openspec:*` are inherited). The title is short: `X.Y <summary>`, where the summary is the part of `<text>` before `; verify` (or its first clause), at most ~80 chars. The full text goes in the description:
   ```bash
   bd create "X.Y <summary>" -t task --parent <epic> -l repo:<key> \
     -d "<full text>" --acceptance "<verification stated in the task; Covers: lines>" --silent
   ```
   Keep a map `X.Y → issue id`.
5. For each `Depends on: A.B` under task `X.Y`: `bd dep add <id of X.Y> <id of A.B>`.
6. Verify: `bd dep cycles` reports none; `bd ready --parent <epic>` shows only tasks without dependencies; the child count equals the checkbox count in `tasks.md`.
7. Record the mapping on the epic: `bd update <epic> --append-notes "tasks.md map: 1.1=<id>, 1.2=<id>, ..."`.
8. End with `bd show <epic>` output summary and the next command: `/mra-build <change-id>`.

## Rules

- `tasks.md` checkboxes stay unticked; beads holds live status.
- A task missing its `[<key>]` tag, or naming a key not declared in `mra-flow.toml`: stop and ask, do not guess the repo.
