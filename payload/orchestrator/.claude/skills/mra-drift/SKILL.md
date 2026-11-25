---
name: mra-drift
description: Use before starting an mra-flow change on a capability that already has a spec, or after pulling commits that touched specified code, to check whether openspec/specs/ still describes it - read-only, any time.
disable-model-invocation: true
argument-hint: [capability] [--since <date|commit>] [--exclude-change <change-id>]
---

# mra-drift — check specs against the real code

Check whether `openspec/specs/` still describes the real behaviour of the code in `$ARGUMENTS`. Read-only: never edit, create or commit any file, and never touch beads.

## Steps

1. List the capabilities in `openspec/specs/` (only the given one, if provided). None → say so, stop.
2. For each capability, find the repos that own it:
   - Locate the most recent archived change that touched it: `openspec/changes/archive/YYYY-MM-DD-*/specs/<capability>/`.
   - Read that change's `tasks.md` for its `[<key>]` tags (or `design.md` Impact) to get the owning repo keys; resolve paths with `.mra-flow/bin/mra-repo list`.
   - No archived change found (the spec predates this orchestrator's history) → ask the user which repos own it.
   - Drop the owning repos whose table in `mra-flow.toml` has `drift = false` (out of scope for this orchestrator's changes): skip every later step for them and list them in the report as "out of scope (`drift = false`), not checked". A capability left with no owning repo gets only that line.
3. Baseline = `--since` if given (a date, or a commit: then use `<commit>..` instead of `--since=` in step 4), otherwise the date of that archived change.
4. Per owning repo: `git -C <path> fetch`, then `git -C <path> log --since=<baseline> --format='%h %an %ad %s' --date=short` on the current branch and on `origin/<default-branch>` (the repo's main clone stays on its default branch). Keep the commits that touch code related to the capability. Highlight commits by authors other than `git -C <path> config user.name`: colleagues' commits never update these specs.
5. For every requirement and scenario of the capability, locate the implementing code (in the repo paths from step 2, or their `.worktrees/<change-id>/<key>` if a change touching it is in flight) and compare. Classify each one:
   - ALIGNED — code matches the spec.
   - DRIFT-SPEC — the code changed on purpose (recent commit, closed beads issue, tests updated): the spec is outdated.
   - DRIFT-CODE — the spec looks right and the code deviates: possible bug.
   - UNVERIFIABLE — implementing code not found or behaviour not determinable statically.
6. List relevant behaviour the code has but the spec does not (UNSPECIFIED). Only list it; do not propose new requirements unless asked.
7. If the capability spans a repo and one of its `depends_on`, both checked (neither dropped in step 2), compare both sides against the `## Contract: <repo> -> <dependency>` section of the archived change's `design.md`, and report inconsistencies.
8. Flag in-flight work on the same capability: an open `openspec/changes/<change-id>/specs/<capability>/`, or a `.worktrees/*` branch touching its repos — a finding there may already be in progress elsewhere. Skip the change named by `--exclude-change` (and its worktrees): it is the caller's own change, e.g. `/mra-archive`'s drift gate.
9. Report, per capability: a table (requirement/scenario, status, evidence as `file:line`, related commit hash and author), then a short summary with counts.
10. Recommend next steps, without executing them:
    - DRIFT-SPEC → a spec-only change: `/mra-propose sync-<capability>-spec-<YYYYMMDD>`, then the Skill tool `openspec-sync-specs` if the correction is needed before other work, and finally the Skill tool `openspec-archive-change` directly — no `/mra-track`, `/mra-build` or `/mra-verify`: there are no code tasks and nothing to track in beads.
    - DRIFT-CODE → a beads bug: `/mra-fix <change-id>` if the capability's change still has an open epic, else `/mra-hotfix`.
    - UNSPECIFIED in an area about to change → include it as an ADDED requirement in the next `/mra-propose`.
    Ask the user before starting any of them.

## Rules

- Show the model at work: `Model: <model> (<role>)` at the phase start, with every subagent dispatch and whenever it changes; see `.mra-flow/docs/agents/model-display.md`.
- Read-only: never edit, create or commit any file, and never create or update a beads issue.
- Report in the user's language; any artifact created afterwards is written in English.
