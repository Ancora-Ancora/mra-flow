---
name: mra-verify
description: Use when all beads tasks of an OpenSpec change in an mra-flow orchestrator are closed and the work must be checked against its specs - phase 5 of the mra-flow workflow.
disable-model-invocation: true
argument-hint: <change-id>
---

# mra-verify — phase 5: verify against specs

Prove the change does what its specs say, in each touched repo and across the contracts between them. Every problem found becomes a beads bug; this phase fixes nothing.

## Steps

1. Call the Skill tool with `superpowers:verification-before-completion`: evidence before claims, for every check below.
2. **Per repo worktree** (`.worktrees/<change-id>/<key>`): run the full test suite, linter and build; record the exact commands and results.
3. **Spec coverage.** For every `#### Scenario:` in `openspec/changes/<change-id>/specs/`, find the test that proves it (via `tasks.md` `Covers:` lines, then the code). A scenario with no passing test is a finding.
4. **Contracts.** For each `## Contract: <repo> -> <dependency>` in `design.md`, check both sides against it (paths, payloads, status codes, error shapes), and run the integration task's end-to-end check against live servers: the committed script whose command the integration task's close reason names (`bd list --parent <epic> --metadata-field task=X.Y --all`). A check with no committed script is a finding (file it); still run the check, with a throwaway script outside the code repos. Unit tests with a mocked client do not count as this check.
5. **UI.** Run the steps of `.claude/skills/mra-qa-ui/SKILL.md` (it cannot be called through the Skill tool) for `<change-id>`: project e2e suite, smoke runner, interactive browsing only where the smoke fails. It files its own findings (label `qa-ui`) and returns `qa-ui: PASS | FAIL | SKIPPED (<reason>)` for the report and the note of step 9.
6. **Code review.** Per worktree, call the Skill tool with `mattpocock-skills:code-review`, fixed point = the branch base (`git -C <path> merge-base change/<change-id> "$(git -C <path> branch --show-current)"`, where `<path>` is the code repo's main clone, which stays on its default branch), spec = the change's `proposal.md`, `specs/`, `design.md`. Tell the reviewers to exclude lockfiles (e.g. `uv.lock`, `pnpm-lock.yaml`, `package-lock.json`) from the diff.
7. `openspec validate <change-id> --strict`.
   **Plan check.** Run the *Plan check* of `/mra-track` (`tasks.md` against the epic's task issues). Each mismatch is a finding labelled `plan-drift` (see step 8).
8. **File findings.** For each real finding (after applying `superpowers:receiving-code-review` judgement):
   ```bash
   bd create "<finding>" -t bug --parent <epic> -l repo:<key>,verify \
     -d "<evidence: command, output, file:line>"
   ```
   Do not add `--deps discovered-from:<epic>`: `--parent` already links the epic, and bd rejects a second dependency on the same issue.
   A Plan check mismatch is filed with the label `plan-drift` instead of `repo:<key>` (add `repo:<key>` only when the task names one): `-l plan-drift,verify`.
9. Record the outcome: `bd update <epic> --append-notes "verify <date>: PASS|FAIL, <n> bugs, qa-ui: <result>, <commands run>"` and `bd update <epic> --set-metadata models="<existing value>; verify=<model>; qa-ui=<model>"` (append to what build recorded; see *Record* in `.mra-flow/docs/agents/model-display.md`).
10. End with a pass/fail table per check, then the next command: `/mra-update <change-id>` if `plan-drift` bugs are open (reconcile the plan before fixing code), else `/mra-fix <change-id>` if bugs are open, else `/mra-archive <change-id>`.

## Rules

- Show the model at work: `Model: <model> (<role>)` at the phase start, with every subagent dispatch and whenever it changes; see `.mra-flow/docs/agents/model-display.md`.
- Do not fix anything here; report and file.
- "Should pass" is not evidence: run it.
