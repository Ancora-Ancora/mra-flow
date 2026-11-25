# mra-flow

A spec-driven workflow for projects split across several code repos: an **orchestrator** repo holds the specs (OpenSpec), decisions, issues (beads) and the `mra-*` Claude Code skills; the code repos are cloned inside it. This repo packages it in two layers:

- **user** (`install.sh --user`, once per machine): personal conventions for every project, orchestrator or not: handoff rules and the SessionStart hook that loads the latest handoff, language, memory, task tracking, and an `Explore` subagent (read-only search on Haiku) that overrides the built-in one. Installed into the Claude Code config dir (`~/.claude`, or `$CLAUDE_CONFIG_DIR`).
- **orchestrator** (`install.sh <dir>`, per orchestrator): the custom OpenSpec workflow: `mra-*` skills, the `mra-flow` schema, `mra-repo`, docs.

## Setup from scratch

On a new machine, do these steps in order, then [Install](#install) and [Verify](#verify).

### 1. Tools

- git, python3 >= 3.11, Node.js >= 22.20 with npm (for OpenSpec), [gh](https://cli.github.com/), [bd (beads)](https://github.com/gastownhall/beads), Claude Code. OpenSpec and the plugins are covered below.

### 2. GitHub access

The repos are private HTTPS repos. Log in once with `gh auth login`. If git has no credential helper, let `gh` supply the token per command:

```bash
git -c credential.helper= -c credential.helper='!gh auth git-credential' push ...
```

`bd dolt push` takes no `-c` flag; pass the same helper through the environment:

```bash
GIT_CONFIG_COUNT=2 \
GIT_CONFIG_KEY_0=credential.helper GIT_CONFIG_VALUE_0= \
GIT_CONFIG_KEY_1=credential.helper GIT_CONFIG_VALUE_1='!gh auth git-credential' \
bd dolt push
```

Or set it once for good: `gh auth setup-git`.

### 3. OpenSpec

OpenSpec is an npm package and needs Node.js 22.20 or newer (OpenSpec 1.16–1.x: 22.12 or newer). Install the CLI globally and check the version:

```bash
npm install -g @fission-ai/openspec@latest
openspec --version         # must be >= 1.16.0
```

If `npm install -g` fails with a permission error, point npm at a user prefix (`npm config set prefix ~/.npm-global` and add `~/.npm-global/bin` to `PATH`) instead of using `sudo`.

The `mra-*` skills call the OpenSpec workflows `explore`, `propose`, `update`, `sync` and `archive`. Enable them in your global profile:

```bash
openspec config profile    # interactive: choose "custom" and tick at least those five
openspec config list       # check the "workflows" list
```

The orchestrator installer runs `openspec init` for a new orchestrator, which generates the OpenSpec skills from this profile. In an orchestrator that already exists, run `openspec update` after changing the profile to regenerate them. To upgrade OpenSpec later, rerun the `npm install` line, then `openspec update` in each orchestrator.

### 4. Claude Code plugins: superpowers and mattpocock-skills

The workflow needs two plugins, both published in the `claude-plugins-official` marketplace (GitHub repo `anthropics/claude-plugins-official`):

- **superpowers**: process skills used by the phases (brainstorming, TDD, systematic debugging, plans, verification before completion, worktrees).
- **mattpocock-skills**: grilling, domain modeling (`GLOSSARY.md`, ADRs), code review, TDD and the `handoff` skill.

The orchestrator installer only *enables* them in `.claude/settings.json`; it does not install them. Install them once per machine, at user scope, from a shell:

```bash
claude plugin marketplace add anthropics/claude-plugins-official   # skip if already listed
claude plugin install superpowers@claude-plugins-official
claude plugin install mattpocock-skills@claude-plugins-official
claude plugin list                                                  # both must be listed
```

Or from inside Claude Code, with the same arguments:

```text
/plugin marketplace add anthropics/claude-plugins-official
/plugin install superpowers@claude-plugins-official
/plugin install mattpocock-skills@claude-plugins-official
```

Restart Claude Code after installing. To upgrade later: `claude plugin marketplace update claude-plugins-official`, then `claude plugin update superpowers@claude-plugins-official` (same for `mattpocock-skills`).

## Install

```bash
gh repo clone Ancora-Ancora/mra-flow ~/.cache/mra-flow
git -C ~/.cache/mra-flow checkout v0.1.29
~/.cache/mra-flow/install.sh --user              # once per machine
~/.cache/mra-flow/install.sh <orchestrator-dir>  # per orchestrator
```

`--user` copies `mra-flow/` and `agents/Explore.md` into the Claude Code config dir, adds `@mra-flow/CLAUDE.md` to its `CLAUDE.md` and the handoff hook to its `settings.json`. The hook also git-ignores `handoff/` in each repo it runs in, through the repo's `.git/info/exclude` (shared by its worktrees), so the rule holds wherever Claude Code runs, a rebuilt dev container included.

For an orchestrator, the installer refuses, changing nothing, if a file it would install already exists with different content. Otherwise it:

- copies the package into `.mra-flow/`, `.claude/skills/mra-*/` and `openspec/schemas/mra-flow/`, and records a checksum of each file in `.mra-flow/manifest`;
- runs `openspec init` if there is no `openspec/` and sets `schema: mra-flow` in `openspec/config.yaml`;
- runs `bd init --skip-agents` and `bd setup claude` if there is no `.beads/` (note: `bd init` makes a commit), and sets `git config beads.role maintainer`;
- adds `@.mra-flow/CLAUDE.md` to `CLAUDE.md`, the required plugins and the spec-drift and update check hooks to `.claude/settings.json`, and `.worktrees/`, `handoff/`, `.beads/issues.jsonl`, `.mra-flow/drift-state.json`, `.mra-flow/update-state.json` to `.gitignore`;
- creates an empty, commented `mra-flow.toml`.

It never rewrites `mra-flow.toml`, `GLOSSARY.md`, `docs/adr/`, `docs/roadmap/` or `openspec/specs/`. Review the result with `git status` and commit it.

## Verify

Start a new Claude Code session in the orchestrator and check:

1. **Handoff hook.** Write a handoff (`/mattpocock-skills:handoff`), then `/clear`: the new session gets it injected exactly once, and its frontmatter turns to `read: true`. The hook is registered only in `~/.claude/settings.json`, not in the project's settings.
2. **Conventions.** `/memory` lists both `~/.claude/mra-flow/CLAUDE.md` and `.mra-flow/CLAUDE.md` as loaded.
3. **Skills.** Typing `/mra` offers the 16 `mra-*` commands. The agent does not list them among its own skills: they set `disable-model-invocation: true`, so only you can start a phase.
4. **Repos.** `.mra-flow/bin/mra-repo list` prints your code repos, dependencies first.
5. **Plugins.** Typing `/superpowers:` and `/mattpocock-skills:` offers their commands.
6. **Spec-drift check hook.** After a code repo's default branch gets a new commit upstream (push it from another clone, or wait for a colleague's), start a new session (or `/clear`): it tells you new commits landed on that repo and recommends `/mra-drift`, without running it. The same hook also reminds you every session, before any repo is declared, to run `mra-repo add`. It is registered in the project's `.claude/settings.json`, not `~/.claude/settings.json`: it needs `mra-flow.toml`, which only exists in an orchestrator.

   A second SessionStart hook, `check-update.py`, asks the mra-flow remote (at most once every 24 hours) for its newest `vX.Y.Z` tag and, when it is newer than the installed `.mra-flow/version`, tells you and recommends the update command without running it. Set `MRA_FLOW_REMOTE` to point it at another remote.

## Update

```bash
~/.cache/mra-flow/install.sh --update [TAG] --user|<orchestrator-dir>   # TAG defaults to the newest v*
```

Files you edited locally are left alone and listed in the report; they stay flagged on later updates. Files dropped from the package are deleted only if unedited. The report warns when a change is in flight (`openspec/changes/*` or `.worktrees/*`).

## Code repos

```bash
.mra-flow/bin/mra-repo add <key> <remote> --description "..." [--depends-on <key> ...] [--path DIR] [--ui-path PATH ...]
.mra-flow/bin/mra-repo clone   # after a fresh clone of the orchestrator: clone missing repos
.mra-flow/bin/mra-repo list    # key, path, depends_on, in integration order
.mra-flow/bin/mra-repo ui-paths <key>   # the repo's UI paths (none: no UI)
.mra-flow/bin/mra-repo integration      # the project's integration command (none: finishing-a-development-branch)
.mra-flow/bin/mra-repo integrate <key> <branch>   # run it for one repo's branch
.mra-flow/bin/mra-effort measure <change-id> [--alias TEXT]   # effective hours per phase, from the session logs
.mra-flow/bin/mra-effort record <initiative> <change-id> --phase build=3.5 ...   # write them into the roadmap
.mra-flow/bin/mra-effort report <initiative>   # totals + docs/roadmap/<initiative>-effort.md (estimate vs. actual)
```

`add` clones the repo, git-ignores it and appends a `[repos.<key>]` table to `mra-flow.toml`. The key is used as task tag `[key]`, beads label `repo:key` and worktree `.worktrees/<change-id>/<key>`.

`ui_paths` (set with `--ui-path`, or by hand in the repo's table, e.g. `ui_paths = ["frontend/"]`) marks a repo's user interface: a change touching it gets browser checks from `/mra-qa-ui` during `/mra-verify` (ADR-0007). Those need Playwright and Chromium where the checks run: `npm i --no-save playwright@<version>`, `npx playwright install chromium`, and on Linux the browser's system libraries, `sudo npx playwright install-deps chromium` (bake them into the dev container image). Per project, record with `bd remember --key qa-ui-<key>` how to start the app, its base URL, how each role logs in (environment variable names, never passwords), the e2e suite command and the interactive browser tool.

`[integration] command = "<command>"` (by hand, a table of its own) replaces `superpowers:finishing-a-development-branch` in `/mra-archive` and `/mra-hotfix`, for projects whose integration has its own rules (e.g. always a pull request on Bitbucket). `mra-repo integrate <key> <branch>` runs it from the orchestrator root as `<command> <key> <repo-path> <branch>`: it must integrate the branch, print the outcome (merge sha or PR url) as its last line and exit non-zero on failure. `mra-repo integration` prints it (nothing when unset).

`drift = false` (by hand in the repo's table) marks a repo that is out of scope for this orchestrator's changes, e.g. one only pulled for reference: the spec-drift check hook never reports its new commits, and `/mra-drift` skips it, listing it as not checked.

## Development

Tests: `python3 -m unittest discover -s tests -t .` (needs only git; fake `bd` and `openspec` are in `tests/fakes/bin`).

`payload/orchestrator/<rel>` is installed at `<orchestrator>/<rel>`; `payload/user/<rel>` at `<claude-config-dir>/<rel>`. Tests never touch the real config: they point `HOME`, `CLAUDE_CONFIG_DIR`, `XDG_CONFIG_HOME` and `GIT_CONFIG_GLOBAL` at a temp dir. Release: bump `VERSION`, run the tests, tag `vX.Y.Z` on that commit, push the tag.
