---
name: mra-fix
description: Use when an OpenSpec change in an mra-flow orchestrator has open beads bugs, or the user reports a defect in it - phase 6 of the mra-flow workflow.
disable-model-invocation: true
argument-hint: <change-id> [bug description]
---

# mra-fix — phase 6: fix bugs

Fix the change's open bugs one at a time, root cause first, test first.

## Steps

1. If `$ARGUMENTS` includes a bug description, file it first: `bd create "<bug>" -t bug --parent <epic> -l repo:<key> -d "<repro>"` (ask which repo if unclear).
2. List work: `bd ready --parent <epic> -t bug`. Empty → go to step 5.
3. For each bug, in priority order:
   - `bd update <id> --claim`
   - **Diagnose** in the bug's worktree `.worktrees/<change-id>/<key>`, with the skill chosen by the table below. Find the root cause before any fix; record it with `bd update <id> --append-notes "debug skill: <name>; root cause: ..."`.
   - **Fix:** call the Skill tool with `superpowers:test-driven-development`. If diagnosis already produced a failing test that reproduces the bug, that test is the RED step: reuse it, do not write a second one. Otherwise write it first. Then the minimal fix, then green.
   - Commit citing `<id>` and `<change-id>`; `bd close <id> --reason "<root cause + fix, commit sha>"`.
   - A new defect discovered on the way: file it with `--deps discovered-from:<id>`, do not fold it in.
4. Repeat step 2 until no bug is ready.
5. End with the next command: `/mra-verify <change-id>` (always re-verify after fixes).

## Choosing the diagnosis skill

Shared with `/mra-hotfix`, which points here by this heading: keep its name.

Call the Skill tool with `mattpocock-skills:diagnosing-bugs` if **any** of these is true; otherwise call it with `superpowers:systematic-debugging`:

| Condition | Why diagnosing-bugs |
|---|---|
| The bug is about slowness or performance | needs a measured feedback loop |
| The bug is intermittent (does not happen on every run) | needs a raised reproduction rate |
| A failing test cannot be written from the bug description on the first attempt | needs its repro-building techniques |
| It is a regression (worked before, a known commit or version) | needs a bisection harness |
| It spans a contract between two code repos and needs an end-to-end repro | needs curl / headless-browser loops |

**Switch mid-way:** if `systematic-debugging` has rejected 3 hypotheses without finding the root cause, stop it and call `mattpocock-skills:diagnosing-bugs`, carrying over what was ruled out. Record the switch in the bug notes.

## Rules

- No fix without a reproducing test.
- If a bug shows a spec or design is wrong, stop and tell the user: the artifacts change first (`/mra-update <change-id>`), then the code.
