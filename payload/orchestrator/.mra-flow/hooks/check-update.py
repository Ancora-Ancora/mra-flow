#!/usr/bin/env python3
"""SessionStart hook: tell the user when a newer mra-flow release exists.

Compares the version installed in this orchestrator (.mra-flow/version) with
the highest release tag (vX.Y.Z) on the mra-flow remote. The remote is asked
at most once every 24 hours (git ls-remote, no fetch); the last check time and
the latest tag seen live in .mra-flow/update-state.json (local, git-ignored),
so the reminder shows every session while an update is pending, without
touching the network. The session is told to recommend the update command,
never to run it.

Never fails the session: not an orchestrator, no version file, an unreachable
remote or an unreadable state file all end the hook silently.
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import time

DEFAULT_REMOTE = "https://github.com/Ancora-Ancora/mra-flow.git"
STATE_PATH = ".mra-flow/update-state.json"
VERSION_PATH = ".mra-flow/version"
CHECK_INTERVAL = 24 * 3600  # seconds between remote checks
TIMEOUT = 8  # seconds; a slow or unreachable remote must not block startup
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
TAG_LINE = re.compile(r"\srefs/tags/v(\d+\.\d+\.\d+)\s*$")


def parse(version: str) -> tuple[int, int, int] | None:
    match = SEMVER.match(version.strip())
    return tuple(int(x) for x in match.groups()) if match else None


def load_state(root: pathlib.Path) -> dict:
    try:
        state = json.loads((root / STATE_PATH).read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}
    return state if isinstance(state, dict) else {}


def save_state(root: pathlib.Path, state: dict) -> None:
    try:
        path = root / STATE_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError:
        pass


def latest_remote_tag(url: str) -> str | None:
    """The highest strict X.Y.Z release on the remote, or None if unreachable or none."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    try:
        done = subprocess.run(
            ["git", "ls-remote", "--tags", "--refs", url, "v*"],
            capture_output=True, text=True, timeout=TIMEOUT, env=env, stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if done.returncode != 0:
        return None
    versions = [m.group(1) for line in done.stdout.splitlines() if (m := TAG_LINE.search(line))]
    return max(versions, key=parse, default=None)


def emit(system_message: str, context: str) -> None:
    json.dump(
        {
            "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context},
            "systemMessage": system_message,
        },
        sys.stdout,
    )


def main() -> int:
    root = pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    if not (root / "mra-flow.toml").is_file():
        return 0
    try:
        installed = (root / VERSION_PATH).read_text(encoding="utf-8").strip()
    except OSError:
        return 0
    if parse(installed) is None:
        return 0

    state = load_state(root)
    latest = state.get("latest") if isinstance(state.get("latest"), str) else None
    checked_at = state.get("checked_at")
    fresh = isinstance(checked_at, (int, float)) and 0 <= time.time() - checked_at < CHECK_INTERVAL
    if not fresh:
        remote = os.environ.get("MRA_FLOW_REMOTE") or DEFAULT_REMOTE
        found = latest_remote_tag(remote)
        if found is not None:
            latest = found
        save_state(root, {"checked_at": time.time(), "latest": latest})

    if latest is None or parse(latest) is None or parse(latest) <= parse(installed):
        return 0
    emit(
        f"mra-flow {latest} is available (installed: {installed})",
        f"A newer mra-flow release exists: {latest} (installed: {installed}); mra-flow "
        "SessionStart check-update hook. Tell the user this at the start of the conversation "
        "and recommend running: "
        f"`git -C ~/.cache/mra-flow fetch --tags && git -C ~/.cache/mra-flow checkout v{latest} "
        f"&& ~/.cache/mra-flow/install.sh {root}`. Do not run it yourself.",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
