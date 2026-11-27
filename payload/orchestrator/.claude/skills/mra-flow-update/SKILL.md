---
name: mra-flow-update
description: Use to update the mra-flow installed in this orchestrator to its newest release, or to a given one, after showing what changes and asking for confirmation.
disable-model-invocation: true
argument-hint: "[X.Y.Z] [--user]"
---

# mra-flow-update — install a newer mra-flow release

Update this orchestrator to the newest mra-flow release, or to the `X.Y.Z` in `$ARGUMENTS`. With `--user`, also update the personal conventions in the Claude Code config dir (`install.sh --user`). The installer is the mra-flow clone at `~/.cache/mra-flow`; missing → tell the user to clone it as the mra-flow README says, and stop.

## Steps

1. **Check.** Run `python3 .mra-flow/hooks/check-update.py check`. Target = the `X.Y.Z` given, else `latest`. Target equal to `installed` and no `--user` → say it is up to date, stop. Target older than `installed` → it is a downgrade: say so and ask before going on.
2. **Changes.** `git -C ~/.cache/mra-flow fetch --tags --quiet`, then `git -C ~/.cache/mra-flow log --no-merges --format='%h %s' v<installed>..v<target>` without the `Release X.Y.Z` commits (`v<target>..v<installed>` for a downgrade). Summarize in a few lines.
3. **Preflight.** Collect, without changing anything:
   - the clone: `git -C ~/.cache/mra-flow status --porcelain` must be empty, or the installer refuses; non-empty → report it and stop;
   - in-flight work: open changes in `openspec/changes/` (not `archive/`) and folders in `.worktrees/`: the updated skills apply to them from now on;
   - local edits to installed files: `git status --porcelain -- .claude/skills .mra-flow`: the installer keeps edited files and lists them;
   - other sessions: Claude Code session logs of this orchestrator written in the last 30 minutes, `find "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/projects/$(pwd | sed 's#[/.]#-#g')" -maxdepth 1 -name '*.jsonl' -mmin -30`. More than one (this session's own log is among them) suggests other active sessions: the update rewrites the skills and hooks they use, and they must be restarted after it.
4. **Confirm.** Ask with AskUserQuestion (header "mra-flow"): "Update to `<target>` now" or "Not now", with the change summary and every preflight warning in the question. "Not now" → stop: the SessionStart hook asks again on the next session start or `/clear`.
5. **Install.** `~/.cache/mra-flow/install.sh --update v<target> <orchestrator root>`. With `--user`, then `~/.cache/mra-flow/install.sh --user` (the clone is already on `v<target>`). Show the installer's report: files copied, kept because edited locally, removed, and its warnings. A failure → show the error and stop; never retry with other options.
6. **Review.** `git status --short`. Propose one commit in this orchestrator with message `Update mra-flow to <target>` (plus a short line on what changed), and commit only after the user confirms.
7. **Reload.** Tell the user to `/clear` this session (or start a new one) and to restart the other sessions, so they load the new skills and hooks.

## Rules

- Show the model at work: `Model: <model> (<role>)` at the phase start, with every subagent dispatch and whenever it changes; see `.mra-flow/docs/agents/model-display.md`.
- Never install without the user's confirmation in step 4, never push, and never edit the files the installer kept as locally edited: list them for the user.
- Never commit, reset or check out anything in `~/.cache/mra-flow` other than through `install.sh --update`.
- Report in the user's language.
