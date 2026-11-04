# mra-flow

A spec-driven workflow for projects split across several code repos: an **orchestrator** repo holds the specs (OpenSpec), decisions, issues (beads) and the `mra-*` Claude Code skills; the code repos are cloned inside it. This repo packages it in two layers:

- **user** (`install.sh --user`, once per machine): personal conventions for every project, orchestrator or not: handoff rules and the SessionStart hook that loads the latest handoff, language, memory, task tracking. Installed into the Claude Code config dir (`~/.claude`, or `$CLAUDE_CONFIG_DIR`).
- **orchestrator** (`install.sh <dir>`, per orchestrator): the custom OpenSpec workflow: `mra-*` skills, the `mra-flow` schema, `mra-repo`, docs.

## Prerequisites

- git, python3 >= 3.11, [bd (beads)](https://github.com/gastownhall/beads), [OpenSpec](https://github.com/Fission-AI/OpenSpec) >= 1.16.0
- OpenSpec workflows enabled in your profile: explore, propose, update, sync, archive
- Claude Code plugins `superpowers` and `mattpocock-skills` from `claude-plugins-official` (the installer declares them in `.claude/settings.json`)

## Install

```bash
gh repo clone Ancora-Ancora/mra-flow ~/.cache/mra-flow
git -C ~/.cache/mra-flow checkout v0.1.0
~/.cache/mra-flow/install.sh --user              # once per machine
~/.cache/mra-flow/install.sh <orchestrator-dir>  # per orchestrator
```

`--user` copies `mra-flow/` into the Claude Code config dir, adds `@mra-flow/CLAUDE.md` to its `CLAUDE.md` and the handoff hook to its `settings.json`, and git-ignores `handoff/` in the global excludes file (`core.excludesFile`, or `~/.config/git/ignore`).

For an orchestrator, the installer refuses, changing nothing, if a file it would install already exists with different content. Otherwise it:

- copies the package into `.mra-flow/`, `.claude/skills/mra-*/` and `openspec/schemas/mra-flow/`, and records a checksum of each file in `.mra-flow/manifest`;
- runs `openspec init` if there is no `openspec/` and sets `schema: mra-flow` in `openspec/config.yaml`;
- runs `bd init --skip-agents` and `bd setup claude` if there is no `.beads/` (note: `bd init` makes a commit), and sets `git config beads.role maintainer`;
- adds `@.mra-flow/CLAUDE.md` to `CLAUDE.md`, the required plugins to `.claude/settings.json`, and `.worktrees/`, `handoff/`, `.beads/issues.jsonl` to `.gitignore`;
- creates an empty, commented `mra-flow.toml`.

It never rewrites `mra-flow.toml`, `GLOSSARY.md`, `docs/adr/` or `openspec/specs/`. Review the result with `git status` and commit it.

## Update

```bash
~/.cache/mra-flow/install.sh --update [TAG] --user|<orchestrator-dir>   # TAG defaults to the newest v*
```

Files you edited locally are left alone and listed in the report; they stay flagged on later updates. Files dropped from the package are deleted only if unedited. The report warns when a change is in flight (`openspec/changes/*` or `.worktrees/*`).

## Code repos

```bash
.mra-flow/bin/mra-repo add <key> <remote> --description "..." [--depends-on <key> ...] [--path DIR]
.mra-flow/bin/mra-repo clone   # after a fresh clone of the orchestrator: clone missing repos
.mra-flow/bin/mra-repo list    # key, path, depends_on, in integration order
```

`add` clones the repo, git-ignores it and appends a `[repos.<key>]` table to `mra-flow.toml`. The key is used as task tag `[key]`, beads label `repo:key` and worktree `.worktrees/<change-id>/<key>`.

## Development

Tests: `python3 -m unittest discover -s tests -t .` (needs only git; fake `bd` and `openspec` are in `tests/fakes/bin`).

`payload/orchestrator/<rel>` is installed at `<orchestrator>/<rel>`; `payload/user/<rel>` at `<claude-config-dir>/<rel>`. Tests never touch the real config: they point `HOME`, `CLAUDE_CONFIG_DIR`, `XDG_CONFIG_HOME` and `GIT_CONFIG_GLOBAL` at a temp dir. Release: bump `VERSION`, run the tests, tag `vX.Y.Z` on that commit, push the tag.
