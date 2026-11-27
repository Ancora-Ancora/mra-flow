---
name: mra-flow-change
description: Use to change the mra-flow workflow itself (an mra-* skill, hook, script, doc or the installer) from an orchestrator - the change is made, tested and committed in the mra-flow source clone, never in the installed copy.
disable-model-invocation: true
argument-hint: <description of the change>
---

# mra-flow-change — change mra-flow in its source clone

Make the change described in `$ARGUMENTS` in the mra-flow source clone, test it and commit it on a branch there. The orchestrator's `.claude/skills/mra-*` and `.mra-flow/` are an installed copy: never edit them (the `guard-installed.py` hook denies it); they change only through `/mra-flow-update`.

## Steps

1. **Source clone.** `MRA_FLOW_SRC`, else `~/mra-flow`; it must hold `payload/orchestrator/`. None → there is no source on this machine: write the change up as an issue for the mra-flow remote (title, problem, proposed change, affected files), show it to the user, stop.
2. **Reach.** The clone is outside the orchestrator: if the file tools cannot read or edit it, ask the user to run `/add-dir <clone>` and wait.
3. **Start clean.** `git -C <clone> status --porcelain` empty (else report it and stop: never stash or discard the user's work). `git -C <clone> fetch --tags --quiet`, then `git -C <clone> switch -c <short-kebab-slug> origin/main`. Read `<clone>/CLAUDE.md` and follow it: it holds the repo's own rules and test command.
4. **Change.** Map each installed path to its source: `<orchestrator>/<rel>` → `<clone>/payload/orchestrator/<rel>`, `~/.claude/<rel>` → `<clone>/payload/user/<rel>`; the installer is `<clone>/installer/`. Make the change there, with tests in `<clone>/tests/` for any behaviour change, and update the docs that describe it (`README.md`, `payload/orchestrator/.mra-flow/CLAUDE.md`, `payload/orchestrator/.mra-flow/docs/mra-flow.md` when an `mra-*` skill or hook changes).
5. **Test.** Run the clone's test command (`CLAUDE.md`); fix until green.
6. **Commit** on the branch, in English, with the identity configured in the clone (never change its git config).
7. **Release, only if the user confirms.** Ask with AskUserQuestion: "Release" or "Keep the branch". Release = fast-forward `main` to the branch, bump `VERSION` (patch unless the user says otherwise), commit `Release X.Y.Z`, annotated tag `vX.Y.Z` (`-m "Release X.Y.Z"`), then `git -C <clone> push origin main vX.Y.Z` with the credentials configured in the clone. A push that fails for credentials → show the error and the command, stop; never push with another account.
8. **Install.** After a release, tell the user to run `/mra-flow-update` in each orchestrator that should get it.

## Rules

- Show the model at work: `Model: <model> (<role>)` at the phase start, with every subagent dispatch and whenever it changes; see `.mra-flow/docs/agents/model-display.md`.
- Never edit the installed copy in the orchestrator, not even to try a change out: test it in the clone.
- Invoking this skill authorizes commits on its branch in the source clone; merging to `main`, tagging and pushing need the user's answer in step 7.
- Report in the user's language; everything written to the clone is in English.
