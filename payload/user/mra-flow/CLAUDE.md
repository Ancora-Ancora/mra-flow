<!-- Installed by `mra-flow install.sh --user` (mra-flow/manifest). A local edit is kept, but this file then stops receiving updates. -->

# Personal conventions (mra-flow)

These apply in every project. A project's own CLAUDE.md can add to them.

## Language

- Every file, code comment, issue and commit message written to a repo is in English. Converse with the user in their language.

## Memory

- Project knowledge (facts about a codebase, its tools and pitfalls): in a repo that uses beads (it has `.beads/`), save it with `bd remember "<insight>" --key <slug>`, so it lives with the repo; otherwise use Claude Code's memory. The user's personal preferences always go to Claude Code's own memory. Do not create `MEMORY.md` files in repos.

## Task tracking

- In a repo that uses beads, beads is the source of truth for task status across sessions. Session todo lists are in-session scratch; mirror their state into beads (`--claim`, `bd close`) as each task progresses.

## Handoff

These rules override the `handoff` skill's own instructions on where and how to save:

- Save to `handoff/ho-<YYYYMMDD-HHMMSS>.md` at the project root (create `handoff/` if missing), not to `$TMPDIR` or `/tmp`. Get the name from `date +%Y%m%d-%H%M%S`.
- The file MUST start with this frontmatter, exactly: `---`, `read: false`, `created: <date -Iseconds>`, `---`.
- Write it in English. In **State**, say what is in flight; for an mra-flow change, give the change id, its phase, the epic id with its `bd epic status` summary, and each worktree's branch and uncommitted changes. Make **Next steps** start with the exact next command (e.g. `/mra-verify <change-id>`).
- `handoff/` is git-ignored through the global git excludes file: never commit it. Never edit an older handoff, and never set `read: true` yourself.
- The SessionStart hook `mra-flow/hooks/load-handoff.py` in the Claude Code config dir (on startup, `/clear` and compaction) injects the newest handoff only if it is `read: false`, then marks it `read: true`. Older handoffs are never loaded.
