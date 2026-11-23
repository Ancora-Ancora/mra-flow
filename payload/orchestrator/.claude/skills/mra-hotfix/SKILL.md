---
name: mra-hotfix
description: Use when a bug is found in a feature of an mra-flow orchestrator whose OpenSpec change is already archived (no open epic), and the code violates a main spec that is still right - rare path of the mra-flow workflow.
disable-model-invocation: true
argument-hint: <bd-id | bug description>
---

# mra-hotfix — fix a bug in an archived feature

One bug, one cycle: track, isolate, diagnose, fix test-first, verify, integrate. The binding spec is the main spec in `openspec/specs/`; this path never edits `openspec/`. A bug whose spec is wrong or silent leaves through *Escalate*.

## Layout

| Item | Value |
|---|---|
| Worktree | `.worktrees/hotfix-<bd-id>/<key>`, only for the repos the bug touches |
| Branch | `hotfix/<bd-id>`, from the code repo's default branch |
| Commit | `<bd-id> hotfix: <summary>` |

## Steps

1. **Track.** If `$ARGUMENTS` is a beads id, `bd show` it. Otherwise find the violated `#### Scenario:` in `openspec/specs/<capability>/spec.md` and file the bug (ask which repo if unclear):
   ```bash
   bd create "<bug>" -t bug -l hotfix,repo:<key>,spec:<capability> \
     -d "Violates openspec/specs/<capability>/spec.md, Scenario: <name>. Repro: <steps, expected, actual>"
   ```
   No `--parent`. If the bug belongs to a change whose epic is still open, stop: that is `/mra-fix <change-id>`. Then `bd update <id> --claim`.
2. **Toolchain preflight**, as in `/mra-build` step 2, for the repos the bug touches.
3. **Worktree.** Call the Skill tool with `superpowers:using-git-worktrees` and apply it with the layout above (`git -C <path> worktree add <orchestrator>/.worktrees/hotfix-<bd-id>/<key> -b hotfix/<bd-id>`).
4. **Diagnose** in the worktree, with the skill chosen by the section *Choosing the diagnosis skill* of `.claude/skills/mra-fix/SKILL.md`. Find the root cause before any fix; record it: `bd update <id> --append-notes "debug skill: <name>; root cause: ..."`. A root cause that is a spec gap → *Escalate*.
5. **Fix.** Call the Skill tool with `superpowers:test-driven-development`. A failing test from diagnosis is the RED step: reuse it. Then the minimal fix, then green. Commit with the message above. A new defect found on the way gets its own `hotfix` issue with `--deps discovered-from:<id>`; it is not folded in.
6. **Verify.** Call the Skill tool with `superpowers:verification-before-completion`. In each touched worktree: full test suite, linter, build; the scenario's test passes. If the bug crosses a contract between two code repos, also run the contract checks of `/mra-verify` step 4. If the fix touches a repo's `ui_paths` (`.mra-flow/bin/mra-repo ui-paths <key>`), run the steps of `.claude/skills/mra-qa-ui/SKILL.md` scoped to the screens the fix touches, with `.worktrees/hotfix-<bd-id>/` in place of `.worktrees/<change-id>/` and the hotfix issue in place of the epic (findings with `--deps discovered-from:<id>`, no `--parent`). Record the evidence: `bd update <id> --append-notes "verify <date>: PASS, <commands and results>"`. A failure goes back to step 4.
7. **Integrate.** Per touched repo, in integration order (`.mra-flow/bin/mra-repo list`: dependencies first): if `.mra-flow/bin/mra-repo integration` prints a command, ask the user to integrate or keep, and integrate with `.mra-flow/bin/mra-repo integrate <key> hotfix/<bd-id>` (its last output line is the outcome; a non-zero exit → stop and report, never retry); otherwise call the Skill tool with `superpowers:finishing-a-development-branch` and let the user choose (merge locally, push + PR, keep). If a push needs credentials, look for notes with `bd memories push`. "Keep" → stop here; the issue stays in progress.
8. **Close:** `bd close <id> --reason "<root cause + fix>; <repo>: <sha/PR>"`.
9. **Notify active changes.** For each integrated repo, list its `change/*` worktrees (`git -C <path> worktree list`). For each such change, find its epic (`bd list -t epic -l openspec:<change-id>`) and append: `bd update <epic> --append-notes "hotfix <id> merged into <repo> main <sha>: merge main into change/<change-id> before /mra-verify"`. Leave the change branches untouched.
10. **Spec drift check.** The fix just changed code behind `<capability>`'s main spec. Recommend `/mra-drift <capability>` to confirm the spec still matches after the fix; the user decides whether to run it now or later.
11. End with a summary: root cause, fix, verify evidence, integration per repo, epics notified.

## Escalate

The spec is wrong or silent, so the fix needs new behaviour: stop before any fix commit.

1. `bd update <id> --append-notes "escalated: spec gap: <what the spec misses>"`; the issue stays open.
2. Remove the hotfix worktrees and the `hotfix/<bd-id>` branches (they hold no commits).
3. End with the next command: `/mra-grill <topic>` if decisions are open, else `/mra-propose <change-id>`. Once `/mra-track` creates the epic, attach the bug: `bd update <id> --parent <epic>`.

## Rules

- No fix without a reproducing test.
- Code goes only to the hotfix worktrees, never to a code repo's main branch.
