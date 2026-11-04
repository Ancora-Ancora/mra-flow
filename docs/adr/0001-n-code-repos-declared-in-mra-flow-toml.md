# Code repos are declared in mra-flow.toml, with depends_on

An orchestrator has any number of code repos (one or more), not a fixed frontend + backend pair. Each repo is declared in `mra-flow.toml` at the orchestrator root with five fields: its key (used as the task tag `[key]`, the beads label `repo:key` and the worktree directory `.worktrees/<change-id>/<key>`), `path`, `remote`, `description` and `depends_on`. Skills derive the integration order (dependencies first) and the required design contracts (a change touching a repo and one of its dependencies needs `## Contract: <repo> -> <dependency>`) from `depends_on`, instead of hard-coding "be before fe" and an "FE↔BE contract".

## Considered Options

- **Discovering repos by scanning the orchestrator root for git-ignored clones.** Rejected: it gives no short stable key (labels would be directory names, broken by a rename), picks up stray clones as code repos, and has no integration order.
- **A table in CLAUDE.md.** Rejected: CLAUDE.md is hand-edited and partly package-managed, so it is a poor source of structured data for scripts.
- **A numeric `order` field.** Rejected: it gives the integration order but not which pairs need a contract, so it would require a contract between any two touched repos, even independent ones.

## Consequences

- Repos are added with `mra-repo add`, which clones, git-ignores and declares the repo in one step; `mra-repo clone` recreates the declared repos after a fresh clone of the orchestrator.
- The file is TOML, not YAML, because Python's standard library reads TOML (`tomllib`) but not YAML; see ADR-0003.
