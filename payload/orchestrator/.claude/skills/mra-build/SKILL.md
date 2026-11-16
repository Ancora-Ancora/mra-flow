---
name: mra-build
description: Use when an OpenSpec change in an mra-flow orchestrator is tracked in beads and ready to implement in its code repos - phase 4 of the mra-flow workflow. Replaces /opsx:apply.
disable-model-invocation: true
argument-hint: <change-id>
---

# mra-build — phase 4: implement with superpowers

Implement the change's beads tasks in the code repos with the superpowers suite. The orchestrator holds no code: all code goes to the worktrees below.

## Layout

The code repos are declared in `mra-flow.toml`; `.mra-flow/bin/mra-repo list` prints `<key> <path> <depends_on>` for each.

| Item | Value |
|---|---|
| Worktree | `.worktrees/<change-id>/<key>` |
| Branch | `change/<change-id>`, from the code repo's default branch |

Only create worktrees for repos that have tasks (a `repo:<key>` label on an open child of the epic).

## Steps

1. Preconditions: the epic for `openspec:<change-id>` exists and has open children. Otherwise stop and suggest `/mra-track <change-id>`.
2. **Toolchain preflight.** For each repo with tasks, run the `--version` of every tool its `CLAUDE.md` build/test commands use (e.g. `uv`, `pnpm`, `node`). If a task needs a browser (e2e, page check), check the browser tool the repo's tests use actually launches (look for setup notes with `bd memories <tool>`). If the change touches a repo's `ui_paths` (`.mra-flow/bin/mra-repo ui-paths <key>`), check now what `/mra-qa-ui` will need (its step 4: `node`, Playwright, the interactive browser tool of `bd memories qa-ui`), so verify does not stop on it. Stop and report what is missing, with the install command; do not start with a broken toolchain.
3. **Worktrees.** Call the Skill tool with `superpowers:using-git-worktrees`, and apply it per repo with the layout above (`git -C <path> worktree add <orchestrator>/.worktrees/<change-id>/<key> -b change/<change-id>`). If a repo has no commits yet (`git -C <path> rev-parse HEAD` fails), stop and ask the user to create an initial commit there first. Reuse existing worktrees.
4. **Plan.** Call the Skill tool with `superpowers:writing-plans`. Inputs: `proposal.md`, `specs/`, `design.md` (its `## Contract:` sections first), `GLOSSARY.md`, relevant ADRs, and `bd children <epic>`. Overrides:
   - Save to `openspec/changes/<change-id>/plan.md`, not `docs/superpowers/plans/`. It stays there and is archived with the change.
   - The plan header's `**Spec:**` field lists `openspec/changes/<change-id>/proposal.md`, `specs/` and `design.md`: the OpenSpec change is the binding authority.
   - One `### Task N: [<bd-id>] <title>` per beads issue: never add, merge or drop tasks. Order them so every task comes after the tasks it depends on (`bd dep list <child-id> <child-id> ...` for all children).
   - Each task states its worktree path (`.worktrees/<change-id>/<key>`) and its commit message: `<bd-id> <change-id>: <summary>`.
   - Execution method is already chosen: subagent-driven. Ask the user only to review the plan.
5. **Execute.** Call the Skill tool with `superpowers:subagent-driven-development` for `plan.md`, with `superpowers:test-driven-development` for every task. The SDD ledger (`.superpowers/sdd/…/progress.md`) is SDD's recovery map; beads stays the source of truth. As controller, around each plan task:
   - **before dispatch:** check the issue is in `bd ready --parent <epic>` (its dependencies are closed); stop and report if it is not. Then `bd update <bd-id> --claim`.
   - **in the implementer brief:** the worktree path and the exact commit message above. The implementer commits; the controller does not commit.
   - **review packages:** SDD's `scripts/` resolve the git repo from the current directory. Run `sdd-workspace` from the orchestrator root (the workspace lives there, next to `plan.md`), but run `review-package` from inside the task's worktree, with the 4th argument `OUTFILE` set to `<workspace>/review-<base7>..<head7>.diff`.
   - **when the ledger records `Task N: complete`:** `bd close <bd-id> --reason "<summary>; commit <sha>"`.
   - **on resume after compaction:** for each `Task N: complete` in the ledger whose issue is still open, close it; never re-dispatch a completed task.
   - **progress bar:** see *Progress bar* below; print it at every step listed there.
6. **Final review, per repo.** Where SDD runs its final whole-branch review, run one per touched worktree (branch `change/<change-id>` against the code repo's default branch), each on the most capable model. File each finding before fixing it, so the fix commit can cite a beads id:
   - a finding fixed in this change → `bd create "<finding>" -t bug --parent <epic> -l repo:<key> -d "Found in the final review of <change-id>: <evidence>"` (no `--deps discovered-from:<epic>`: `--parent` already links the epic, and bd rejects a second dependency on it); commit message `<bug-id> <change-id>: <summary>`;
   - a finding parked as minor → `bd create "<finding>" -t task -l repo:<key>,needs-triage --deps discovered-from:<epic>`, outside the epic, so it does not block archive.
7. **Save the rulings.** Before SDD deletes its workspace, copy every `Ruling:` line of `<workspace>/progress.md` into the epic: `bd update <epic> --append-notes "SDD rulings: ..."`. The ledger dies with the workspace; the epic keeps the decisions.
8. **Stop.** After the final reviews, do NOT call `superpowers:finishing-a-development-branch`, even though SDD says to: integration happens in `/mra-archive`, after verify. Leave the worktrees and branches in place.
9. **Mid-build discoveries:**
   - a defect outside the current task: `bd create "<bug>" -t bug --parent <epic> -l repo:<key> --deps discovered-from:<current id>`, then continue;
   - a **spec gap** (the spec or design is wrong, or silent on behaviour a task must decide): stop the task, tell the user, and run the `/mra-update <change-id>` steps (artifacts, then beads reconcile). Then update the stale `plan.md` tasks and resume. Never settle a spec gap in code alone.
10. When every task issue of the epic is closed, end with the next command: `/mra-verify <change-id>`.

## Progress bar

From plan approval (step 4) until the last task closes, every message the controller writes to the user starts with one progress line, so the user always sees where the build stands. The line holds two bars side by side: the epic's tasks, then the current task.

```
mra-build <change-id> tasks [████████░░░░░░░░░░░░] 4/10 · Task 5: [<bd-id>] <title> · task [██████░░░░] ~60% spec review
```

- **Tasks bar:** 20 cells; filled cells = `round(20 × closed / total)`, where `closed` and `total` count the epic's children (`bd children <epic>`), so the bar survives compaction and grows when step 6 adds bugs to the epic. Read them from beads, never from memory.
- **Current task:** the plan task being worked on, with its stage: `claimed` → `implementing` → `spec review` → `quality review` → `fixing review` → `closed`. During step 6 it reads `final review <key>` (or the fix being worked on); with nothing in flight, `idle`.
- **Task bar:** 10 cells for the current task's own progress, with the percentage after it. The controller cannot see inside a running subagent, so the percentage is an estimate from the stage: `claimed` ~5%, `implementing` 10-50%, `spec review` / `quality review` 60-80%, `fixing review` ~85%, `closed` 100%. Prefix it with `~` while it is an estimate. Refine it as reports arrive (e.g. a fix round lowers it back into the review range), and never let it reach 100% before `bd close`. With nothing in flight, the bar is full after a close and empty when idle before the first dispatch.
- **When:** after plan approval, before each dispatch, after each implementer or reviewer report, after each `bd close`, and on resume after compaction. Print it as plain text (a fenced code block), not through a todo list: beads stays the source of truth.

## Rules

- Beads is the source of truth for task status; session todo lists are scratch only.
- Do not tick `tasks.md`, and do not run `/opsx:apply`.
- Do not merge, push, or open PRs here, and do not run `finishing-a-development-branch`; that is `/mra-archive`.
