# The handoff hook git-ignores handoff/ per repo

ADR-0005 had `install.sh --user` add `handoff/` to the global git excludes file. That file belongs to the machine's git config, which a dev container does not keep: the Claude Code config dir is usually bind-mounted from the host, but `~/.gitconfig` is copied in and `~/.config/git/ignore` is not there at all, so after a rebuild handoffs show up as untracked files in any repo that does not ignore them itself. Instead, the SessionStart handoff hook adds `handoff/` to the current repo's `.git/info/exclude` (the common git dir, so worktrees share it) on every session start. That file lives inside the project, so the rule holds wherever the hook runs, and nothing in the user's git config is changed. This supersedes the global-excludes part of ADR-0005.

## Consequences

- The installer no longer writes the global excludes file; lines an earlier version added there are left in place, harmless.
- A repo is covered only after one Claude Code session has started in it; before that, `handoff/` cannot exist anyway, since only a session writes handoffs.
- Orchestrators keep `handoff/` in their committed `.gitignore`, which also covers collaborators who do not use the user layer.
