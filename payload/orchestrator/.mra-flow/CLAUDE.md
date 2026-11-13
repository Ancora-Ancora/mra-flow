<!-- Installed by mra-flow (.mra-flow/manifest). A local edit is kept, but this file then stops receiving updates. -->

## Orchestrator layout

This repo is an **orchestrator**. It holds no application code.

| Path | Holds | Git |
|---|---|---|
| `openspec/` | specs, changes, the `mra-flow` schema | this repo |
| `docs/adr/`, `GLOSSARY.md` | architecture decisions and domain language, shared by all code repos | this repo |
| `.beads/` | the beads issue database for all code repos | this repo |
| `.claude/skills/mra-*`, `.mra-flow/` | the workflow skills, hook, docs and `mra-repo`, installed by mra-flow | this repo |
| `mra-flow.toml` | the repo registry: one `[repos.<key>]` table per code repo, with `path`, `remote`, `description`, `depends_on` | this repo |
| each repo's `path` | a code repo | separate repo, git-ignored here |
| `.worktrees/<change-id>/<key>` | per-change worktrees of the code repos, branch `change/<change-id>` | git-ignored here |

Build, test and stack conventions live in each code repo's own `CLAUDE.md`. `.mra-flow/bin/mra-repo list` prints the code repos in integration order (dependencies first); `mra-repo add` declares a new one and `mra-repo clone` restores missing clones.

## Workflow

Every feature goes through the `mra-flow` workflow (diagram: `.mra-flow/docs/mra-flow.md`; keep it in sync when an `mra-*` skill changes). Start each phase with its command:

| Phase | Command | Output |
|---|---|---|
| (optional) explore | `/mra-explore [idea]` | understanding only, nothing written |
| 1. grill | `/mra-grill <topic>` | `GLOSSARY.md` terms, ADRs in `docs/adr/` |
| 2. propose | `/mra-propose <change-id>` | OpenSpec change: proposal, specs, design, tasks |
| 3. track | `/mra-track <change-id>` | beads epic + one issue per task |
| 4. build | `/mra-build <change-id>` | code in the worktrees, one commit per issue |
| 5. verify | `/mra-verify <change-id>` | pass/fail report, findings filed as beads bugs |
| 6. fix | `/mra-fix <change-id> [bug]` | bugs fixed test-first; then back to verify |
| 7. archive | `/mra-archive <change-id>` | branches integrated, change archived, epic closed |
| any time | `/mra-update <change-id>` | revised artifacts, beads reconciled |
| rare | `/mra-sync <change-id>` | delta specs merged into main specs before archive |
| rare | `/mra-hotfix <bd-id \| bug>` | bug in an archived feature fixed test-first, verified and integrated |
| any time | `/mra-drift [capability]` | drift report: specs vs. real code, read-only |
| end of session | `/mattpocock-skills:handoff [next focus]` | `handoff/ho-<datetime>.md` (`read: false`), auto-loaded once by the next session (handoff rules: installed with `install.sh --user`) |

Rules:

- Never implement through `/opsx:apply` or the `openspec-apply-change` skill: implementation is `/mra-build`.
- An `mra-*` command whose argument is a question instead of what its argument hint asks for gets an answer in the context of the current phase; the phase is not restarted.
- Write code only in `.worktrees/<change-id>/<key>` (or `.worktrees/hotfix-<bd-id>/<key>` for `/mra-hotfix`), never in this repo and never on the code repos' main branch.
- The other `/opsx:*` and `/mattpocock-skills:*` commands stay available for one-off use; the `mra-*` commands are the default path.

### Spec drift

`openspec/specs/` is written once per change; colleagues' other work on the code repos never touches it, so it can go stale.

- Before `/mra-grill` or `/mra-propose` on a capability that already has a spec, run `/mra-drift <capability>` and resolve DRIFT-SPEC items first (both skills ask this on your behalf; you can also run it yourself first).
- After `/mra-hotfix`, or any manual change that alters specified behaviour, run `/mra-drift <capability>` and sync the spec.

### How this overrides the beads defaults

The beads context injected by `bd prime` is subordinate to this section (task tracking and memory rules come from the user-level conventions):

- **When issues are created:** only in `/mra-track`, `/mra-build`, `/mra-verify`, `/mra-fix`, `/mra-hotfix` and `/mra-update`. Exploring, grilling and proposing create no issues.
- **Creating issues:** sequentially, from the skill doing the work; no parallel subagents for issue creation.
- **Commit authority:** invoking `/mra-build` or `/mra-fix` authorizes commits on the `change/<change-id>` branches inside `.worktrees/`. Invoking `/mra-hotfix` authorizes commits on its `hotfix/<bd-id>` branches. Push, merge and PRs happen only in `/mra-archive` and at the end of `/mra-hotfix`, with the user choosing the option per repo. Commits in this orchestrator repo always need the user's confirmation.

## Agent skills

### Issue tracker

Issues live in beads (`bd`), in this orchestrator repo's database, and cover all code repos. See `.mra-flow/docs/agents/issue-tracker.md`.

### Triage labels

The five default canonical labels (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`), applied as beads labels. See `.mra-flow/docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` + `docs/adr/` at the orchestrator root, shared by all code repos. See `.mra-flow/docs/agents/domain.md`.
