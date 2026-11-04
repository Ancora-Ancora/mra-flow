---
name: mra-update
description: Use when an existing OpenSpec change in the low-and-slow orchestrator must be revised - new decisions, a wrong spec or design found during build or fix, or artifacts out of sync with each other - in the mra-flow workflow.
disable-model-invocation: true
argument-hint: <change-id> [what changes]
---

# mra-update — revise a change and keep beads in sync

Revise the change's artifacts, then reconcile the work already tracked or built from them.

## Steps

1. If the revision comes from a new hard-to-reverse decision, record it first (Skill tool: `mattpocock-skills:domain-modeling`) so the artifacts can cite the ADR.
2. Call the Skill tool with `openspec-update-change` for `$ARGUMENTS` and follow it. The `mra-flow` schema rules still apply (FE↔BE Contract, `[be]`/`[fe]` tags, `Depends on:` / `Covers:`).
3. `openspec validate <change-id> --strict` passes.
4. **Reconcile beads** if an epic `openspec:<change-id>` exists (`bd children <epic>`, map in the epic notes):
   - new tasks → run the `/mra-track <change-id>` steps (idempotent: creates only what is missing);
   - removed or rewritten tasks → list the affected issue ids and their status, and ask the user before closing (`bd close <id> --reason "dropped by update: ..."`) or editing them; closed work invalidated by the change becomes a new task, not a reopened one;
   - changed dependencies → `bd dep add` / `bd dep remove`.
5. If `openspec/changes/<change-id>/plan.md` exists, flag the plan tasks the revision makes stale; the plan is updated in `/mra-build` before more work runs.
6. End with a summary of artifact changes, beads changes, and the next command for the phase the change is in.

## Rules

- Never edit code here.
