#!/usr/bin/env python3
"""SessionStart hook: notice new commits on the code repos' default branches.

For each repo in mra-flow.toml, asks the remote (no fetch, no local writes other
than our own state file) for the SHA its default branch HEAD points to, and
compares it with the SHA last seen for that repo. A repo seen for the first
time is recorded silently: there is nothing yet to compare it with. Otherwise,
a changed SHA means colleagues' commits may have landed since the last check,
so openspec/specs/ may be stale; the session is told to recommend /mra-drift,
never to run it.

Never fails the session: a missing mra-flow.toml, an unreachable remote or an
unreadable state file all end the hook silently.
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import tomllib

STATE_PATH = ".mra-flow/drift-state.json"
TIMEOUT = 8  # seconds per repo; a slow or unreachable remote must not block startup


def load_repos(root: pathlib.Path) -> dict[str, dict]:
    toml = root / "mra-flow.toml"
    if not toml.is_file():
        return {}
    try:
        data = tomllib.loads(toml.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError:
        return {}
    return data.get("repos", {})


def load_state(root: pathlib.Path) -> dict[str, str]:
    path = root / STATE_PATH
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}


def save_state(root: pathlib.Path, state: dict[str, str]) -> None:
    path = root / STATE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def remote_head_sha(path: pathlib.Path) -> str | None:
    """The SHA the remote's default branch currently points to, or None if unreachable."""
    try:
        done = subprocess.run(
            ["git", "-C", str(path), "ls-remote", "--symref", "origin", "HEAD"],
            capture_output=True, text=True, timeout=TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if done.returncode != 0:
        return None
    match = re.search(r"^([0-9a-f]{40})\s+HEAD\s*$", done.stdout, re.MULTILINE)
    return match.group(1) if match else None


def main() -> int:
    root = pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    repos = load_repos(root)
    if not repos:
        return 0
    state = load_state(root)
    changed = []
    for key, repo in sorted(repos.items()):
        path = root / repo.get("path", key)
        if not path.is_dir():
            continue
        sha = remote_head_sha(path)
        if sha is None:
            continue
        previous = state.get(key)
        if previous is not None and previous != sha:
            changed.append(key)
        state[key] = sha
    save_state(root, state)

    if not changed:
        return 0
    repo_list = ", ".join(changed)
    context = (
        f"New commits landed on the default branch of: {repo_list} (mra-flow SessionStart "
        "check-drift hook). openspec/specs/ may now be stale for capabilities those repos own. "
        "Tell the user this at the start of the conversation and recommend running /mra-drift "
        "to check; do not run it yourself."
    )
    json.dump(
        {
            "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context},
            "systemMessage": f"New commits on {repo_list} since the last check — consider /mra-drift",
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
