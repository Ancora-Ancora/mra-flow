---
name: mra-update
description: Use when an existing OpenSpec change in an mra-flow orchestrator must be revised - new decisions, a wrong spec or design found during build or fix, or artifacts out of sync with each other - in the mra-flow workflow.
disable-model-invocation: true
argument-hint: <change-id> [what changes]
---

# mra-update — revise a change and keep beads in sync

Revise the change's artifacts, then reconcile the work already tracked or built from them.

## Steps

1. If the revision hinges on an open question, settle it first: an external fact (library, API, standard, version) → recommend `/mra-research <question> --change <change-id>`; a design question nobody can settle by talking (a state model, or what a UI should look like) → recommend `/mra-prototype <question>`. Use the finding or verdict as the new decision. A revision that adds or changes a screen gets its UI preview first, as `.mra-flow/docs/agents/ui-preview.md` says, and its `preview:` line in `design.md`. A revision that adds a module other changes will reuse, places a seam, or changes the interface of a module in `design.md`'s `## Module design` gets its module design first, as `.mra-flow/docs/agents/module-design.md` says (Skill tool: `mattpocock-skills:codebase-design`, its `DESIGN-IT-TWICE.md`), and its `### <module>` entry updated.
2. If the revision comes from a new hard-to-reverse decision, record it first (Skill tool: `mattpocock-skills:domain-modeling`) so the artifacts can cite the ADR.
3. Call the Skill tool with `openspec-update-change` for `$ARGUMENTS` and follow it. The `mra-flow` schema rules still apply (`## Contract:` sections, `[<key>]` tags, `Depends on:` / `Covers:`).
4. `openspec validate <change-id> --strict` passes.
5. **Reconcile beads** if an epic `openspec:<change-id>` exists. Tasks and issues are linked by the issue's `task` metadata (`X.Y`); see *Plan check* in `/mra-track`.
   - **Numbers are stable:** in `tasks.md`, never renumber an existing task. A new task takes the next free number in its group; a removed task's number is never reused. If step 3 renumbered tasks, restore the old numbers before reconciling.
   - new tasks → run the `/mra-track <change-id>` steps (idempotent: creates only what is missing);
   - removed tasks → list the affected issue ids and their status, and ask the user, then `bd update <id> --set-metadata dropped=true` and `bd close <id> --reason "dropped by update: ..."`;
   - rewritten tasks → list the affected issue ids and their status, and ask the user, then update the issue to the new text (`--title`, `--description`, `--acceptance`, labels). Closed work invalidated by the change becomes a new task, not a reopened one;
   - changed dependencies → `bd dep add` / `bd dep remove`;
   - finally, run the *Plan check* of `/mra-track`: it must report no mismatch. Close each open `plan-drift` bug of the epic it no longer reports: `bd close <id> --reason "reconciled by update: ..."`.
6. If `openspec/changes/<change-id>/plan.md` exists, flag the plan tasks the revision makes stale; the plan is updated in `/mra-build` before more work runs.
7. End with a summary of artifact changes, beads changes, and the next command for the phase the change is in.

## Rules

- Show the model at work: `Model: <model> (<role>)` at the phase start, with every subagent dispatch and whenever it changes; see `.mra-flow/docs/agents/model-display.md`.
- Never edit code here.
- Never tick `tasks.md` checkboxes here; beads holds live status.
