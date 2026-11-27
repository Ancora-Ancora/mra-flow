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
2. **Idempotency.** `bd list -t epic -l openspec:<change-id> --all --json`. If an epic exists, list its children (`bd children <epic> --json`) and only create what is missing, matching tasks to children by their `task` metadata (`X.Y`), never by title; never duplicate. A child with metadata `dropped` was removed by `/mra-update`: never recreate it.
3. Create the epic. If the change id is a slice of a roadmap (`.mra-flow/docs/agents/roadmap.md`, *Finding the slice of a change*) and its slice epic exists, promote it instead, as *Promotion* in that file says, then set the row's Status to `in progress` and its Epic, and its start: `.mra-flow/bin/mra-effort record <initiative> <change-id> --start "<start>"`, with `<start>` from `.mra-flow/bin/mra-effort measure <change-id> --json` (its grill, usually; plus `--alias <grill topic>` when the grill did not name the change). Otherwise:
   ```bash
   bd create "<change-id>: <proposal title>" -t epic -l openspec:<change-id> \
     --spec-id openspec/changes/<change-id> -d "<proposal Why, 1-3 lines>" --silent
   ```
4. For each checkbox task `X.Y [<key>] <text>`, create a child (labels `openspec:*` are inherited). The title is short: `X.Y <summary>`, where the summary is the part of `<text>` before `; verify` (or its first clause), at most ~80 chars. The full text goes in the description:
   ```bash
   bd create "X.Y <summary>" -t task --parent <epic> -l repo:<key> \
     -d "<full text>" --acceptance "<verification stated in the task; Covers: lines>" \
     --metadata '{"task":"X.Y"}' --silent
   ```
   The `task` metadata is the one link between a task and its issue: every other phase finds the issue of `X.Y` with `bd list --parent <epic> --metadata-field task=X.Y --all`.
   Always write it as a JSON string with `--metadata '{"task":"X.Y"}'` (on create and on update; it merges with the other keys). Never `--set-metadata task=X.Y`: bd parses that value, so `2.10` is stored as the number `2.1` and collides with task 2.1.
5. For each `Depends on: A.B` under task `X.Y`: `bd dep add <id of X.Y> <id of A.B>`.
6. Verify: `bd dep cycles` reports none; `bd ready --parent <epic>` shows only tasks without dependencies; the *Plan check* below reports no mismatch.
7. End with `bd show <epic>` output summary and the next command: `/mra-build <change-id>`.

## Plan check

Shared with `/mra-update`, `/mra-verify` and `/mra-archive`, which point here by this heading: keep its name. Read-only: it reports, it changes nothing.

`tasks.md` owns the plan (what to do), beads owns the status. The check compares the checkbox tasks of `tasks.md` with the epic's planned children: `bd list --parent <epic> -t task --has-metadata-key task --all --json`, leaving out the children with metadata `dropped`.

Legacy epics, tracked before the `task` metadata existed, keep the link in a `tasks.md map: 1.1=<id>, ...` line of the epic notes (the last one wins). Before the first check on such an epic, copy it into metadata (`bd update <id> --metadata '{"task":"X.Y"}'`) and say so in the report.

Report one line per mismatch:

| Mismatch | Usual cause |
|---|---|
| a task `X.Y` with no child | task added to `tasks.md` by hand, outside `/mra-update` |
| a child whose `X.Y` is not in `tasks.md` | task removed or renumbered by hand |
| two children with the same `X.Y` | duplicate tracking |
| child description or acceptance differs from the task text, its verification or its `Covers:` lines | task rewritten by hand |
| child `repo:<key>` differs from the task's `[<key>]` | task moved to another repo by hand |
| child dependencies differ from the task's `Depends on:` | dependencies changed by hand |
| a `-t task` child of the epic with no `task` metadata | planned work tracked outside `tasks.md` |
| a child whose `task` metadata is a number, not a string (`2.1` where the title says `2.10`) | written with `--set-metadata task=X.Y`, which parses the value |
| a ticked checkbox before `/mra-archive` | status written into the plan |

Bugs (`-t bug`) are never part of the check: they live only in beads. Every mismatch is fixed by `/mra-update <change-id>`, never by editing the issue or `tasks.md` alone.

## Rules

- Show the model at work: `Model: <model> (<role>)` at the phase start, with every subagent dispatch and whenever it changes; see `.mra-flow/docs/agents/model-display.md`.
- `tasks.md` checkboxes stay unticked; beads holds live status.
- Task numbers are stable once tracked: never renumber a task, never reuse the number of a removed one.
- A task missing its `[<key>]` tag, or naming a key not declared in `mra-flow.toml`: stop and ask, do not guess the repo.
