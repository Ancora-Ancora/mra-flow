#!/usr/bin/env python3
"""PreToolUse hook: keep the installed copy of mra-flow read-only.

The orchestrator holds a copy of mra-flow (ADR-0002): `.claude/skills/mra-*` and
`.mra-flow/`, listed with their checksums in `.mra-flow/manifest`. A session
that edits that copy forks the workflow: the next update keeps the edited file
as "edited locally" and the change never reaches mra-flow or other projects.
So an Edit/Write/MultiEdit/NotebookEdit of such a file is denied, and the
session is pointed at the same file in the mra-flow source clone
(`MRA_FLOW_SRC`, default `~/mra-flow`) and at `/mra-flow-change`.

Guarded: every path in the manifest, the installer's own `.mra-flow/manifest`
and `.mra-flow/version`, and any new file under `.claude/skills/mra-*` or
`.mra-flow/` (a local skill or script would be a fork too). Not guarded: the
hooks' local state files (`.mra-flow/*-state.json`).

Never fails the session: not an orchestrator, unreadable input or manifest all
let the tool call through.
"""
import json
import os
import pathlib
import sys

MANIFEST_PATH = ".mra-flow/manifest"
INSTALLER_STATE = (".mra-flow/manifest", ".mra-flow/version")
DEFAULT_SOURCE = "~/mra-flow"
REMOTE = "https://github.com/Ancora-Ancora/mra-flow"


def installed_files(root: pathlib.Path) -> set[str]:
    try:
        data = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
        files = data.get("files", {}) if isinstance(data, dict) else {}
        return set(files) if isinstance(files, dict) else set()
    except (OSError, ValueError):
        return set()


def guarded(rel: str, installed: set[str]) -> bool:
    if rel in installed or rel in INSTALLER_STATE:
        return True
    if rel.startswith(".mra-flow/"):
        return not rel.endswith("-state.json")
    return rel.startswith(".claude/skills/mra-")


def source_clone() -> pathlib.Path | None:
    """The mra-flow source clone on this machine, if there is one."""
    path = pathlib.Path(os.path.expanduser(os.environ.get("MRA_FLOW_SRC") or DEFAULT_SOURCE))
    return path if (path / "payload" / "orchestrator").is_dir() else None


def target_path(event: dict) -> str | None:
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    path = tool_input.get("file_path") or tool_input.get("notebook_path")
    return path if isinstance(path, str) and path else None


def deny(reason: str) -> None:
    json.dump({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}, sys.stdout)


def main() -> int:
    root = pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    if not (root / "mra-flow.toml").is_file():
        return 0
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    path = target_path(event) if isinstance(event, dict) else None
    if path is None:
        return 0
    cwd = pathlib.Path(event.get("cwd") or root)
    try:
        rel = (cwd / os.path.expanduser(path)).resolve().relative_to(root).as_posix()
    except ValueError:
        return 0  # outside the orchestrator, e.g. the mra-flow source clone itself
    if not guarded(rel, installed_files(root)):
        return 0

    source = source_clone()
    where = (f"Make the change in the mra-flow source clone instead: "
             f"`{source / 'payload' / 'orchestrator' / rel}` "
             "(run `/add-dir` on the clone if this session cannot reach it), or use "
             "`/mra-flow-change <description>`; then release it and run `/mra-flow-update` here."
             if source else
             "There is no mra-flow source clone on this machine (`MRA_FLOW_SRC`, default "
             f"`{DEFAULT_SOURCE}`): describe the change to the user and propose an issue on "
             f"{REMOTE}/issues instead.")
    deny(f"`{rel}` is part of the mra-flow copy installed in this orchestrator: editing it here "
         "forks the workflow, and the next mra-flow update would keep the edit as a local one "
         f"without ever sharing it. {where}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
