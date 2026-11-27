---
name: mra-flow-version-check
description: Use to find out whether a newer mra-flow release than the one installed in this orchestrator exists, and what it changes - read-only, any time.
disable-model-invocation: true
argument-hint: ""
---

# mra-flow-version-check — is a newer mra-flow release available?

Ask the mra-flow remote now (not the SessionStart hook's cached answer) for its newest release and compare it with the version installed in this orchestrator. Read-only: change nothing but the hook's state file `.mra-flow/update-state.json`, which the check refreshes.

## Steps

1. Run `python3 .mra-flow/hooks/check-update.py check`. It prints `installed`, `latest` and `status` (`up to date`, `update available`, `update available (ignored)`, `unknown`); exit code 2 means the remote was unreachable and `latest` is the last one seen.
2. If an update is available, show what it changes. The mra-flow clone the installer runs from is `~/.cache/mra-flow` (missing → say so and skip this step):
   - `git -C ~/.cache/mra-flow fetch --tags --quiet` (fetch only: never check out or change the clone's working tree here);
   - `git -C ~/.cache/mra-flow log --no-merges --format='%h %s' v<installed>..v<latest>`, leaving out the `Release X.Y.Z` commits.
   Summarize the changes in a few lines, grouped by what the user notices (skills, hooks, installer, docs).
3. Report: installed version, latest version, the summary, and the next step: `/mra-flow-update` to install it (`/mra-flow-update <X.Y.Z>` for a specific release). When the release was ignored, say so: the SessionStart hook stays silent until a newer one appears.

## Rules

- Show the model at work: `Model: <model> (<role>)` at the phase start, with every subagent dispatch and whenever it changes; see `.mra-flow/docs/agents/model-display.md`.
- Never run the installer or `/mra-flow-update` from here: recommend it.
- Report in the user's language.
