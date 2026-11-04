# Harness conventions are a separate user-level layer

mra-flow holds two different things: a custom OpenSpec workflow, which only makes sense in an orchestrator, and the user's personal conventions for the Claude Code harness (handoff rules and the SessionStart hook that loads the latest handoff, language, memory, task tracking), which apply in every project, orchestrator or not. The conventions are therefore installed once per machine by `install.sh --user` into the Claude Code config dir (`~/.claude`, or `$CLAUDE_CONFIG_DIR`): `mra-flow/` there, imported by `~/.claude/CLAUDE.md`, the hook in `~/.claude/settings.json`, and `handoff/` in the global git excludes file. The orchestrator layer keeps only the workflow; it no longer wires the hook into the project's `.claude/settings.json` (this supersedes that part of ADR-0002).

## Consequences

- A repo that is not an orchestrator, such as this one, still gets handoffs, the language rule and the memory rule.
- The memory and task-tracking rules are written conditionally ("in a repo that uses beads"), since not every project has beads.
- An orchestrator that still wires its own copy of the handoff hook must drop it, or the handoff could be injected twice.
