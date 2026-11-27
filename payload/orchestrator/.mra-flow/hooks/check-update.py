#!/usr/bin/env python3
"""SessionStart hook and CLI: is a newer mra-flow release available?

Compares the version installed in this orchestrator (.mra-flow/version) with
the highest release tag (vX.Y.Z) on the mra-flow remote (git ls-remote, no
fetch). The last check time, the latest tag seen and the release the user chose
to ignore live in .mra-flow/update-state.json (local, git-ignored).

Usage:
  check-update.py            SessionStart hook: asks the remote at most once every
                             CHECK_INTERVAL; while a newer release is pending (and not
                             ignored) it tells the session to ask the user whether to
                             update now, later or ignore that release. Repeats every
                             session start and /clear until then.
  check-update.py check      asks the remote now and prints installed, latest and status
                             (/mra-flow-version-check, /mra-flow-update).
  check-update.py ignore V   no notice for releases up to V (the user's "Ignore").

The hook never fails the session: not an orchestrator, no version file, an
unreachable remote or an unreadable state file all end it silently.
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
CHECK_INTERVAL = 4 * 3600  # seconds between remote checks from the hook
TIMEOUT = 8  # seconds; a slow or unreachable remote must not block startup
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
TAG_LINE = re.compile(r"\srefs/tags/v(\d+\.\d+\.\d+)\s*$")


def parse(version: str) -> tuple[int, int, int] | None:
    match = SEMVER.match(version.strip()) if isinstance(version, str) else None
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


def installed_version(root: pathlib.Path) -> str | None:
    try:
        installed = (root / VERSION_PATH).read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return installed if parse(installed) else None


def refresh(root: pathlib.Path, state: dict, force: bool) -> tuple[str | None, bool]:
    """The latest release known, asking the remote if forced or the last check is old.
    Returns (latest, reached): reached is False when the remote was asked and failed."""
    latest = state.get("latest") if parse(state.get("latest")) else None
    checked_at = state.get("checked_at")
    fresh = isinstance(checked_at, (int, float)) and 0 <= time.time() - checked_at < CHECK_INTERVAL
    if fresh and not force:
        return latest, True
    found = latest_remote_tag(os.environ.get("MRA_FLOW_REMOTE") or DEFAULT_REMOTE)
    if found is not None:
        latest = found
    state.update(checked_at=time.time(), latest=latest)
    save_state(root, state)
    return latest, found is not None


def newer(latest: str | None, than: str | None) -> bool:
    return parse(latest) is not None and (parse(than) is None or parse(latest) > parse(than))


def emit(system_message: str, context: str) -> None:
    json.dump(
        {
            "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context},
            "systemMessage": system_message,
        },
        sys.stdout,
    )


def hook(root: pathlib.Path) -> int:
    installed = installed_version(root)
    if installed is None:
        return 0
    state = load_state(root)
    latest, _ = refresh(root, state, force=False)
    if not newer(latest, installed) or not newer(latest, state.get("ignored")):
        return 0
    emit(
        f"mra-flow {latest} is available (installed: {installed}) — update now, later or ignore?",
        f"A newer mra-flow release exists: {latest} (installed: {installed}); mra-flow SessionStart "
        "check-update hook. Before anything else in your first reply, ask the user with "
        'AskUserQuestion (header "mra-flow") what to do, and wait for the answer:\n'
        f'- "Update now": follow `.claude/skills/mra-flow-update/SKILL.md` for {latest}; it asks '
        "for confirmation again before installing. Updating rewrites the skills and hooks other "
        "Claude Code sessions in this orchestrator are using, so the user may prefer later.\n"
        '- "Later": do nothing; the question comes back on the next session start or /clear.\n'
        f'- "Ignore {latest}": run `python3 .mra-flow/hooks/check-update.py ignore {latest}`; '
        "only a newer release is notified again.\n"
        "Then go on with the user's request. Never update without the user's answer.",
    )
    return 0


def check(root: pathlib.Path) -> int:
    installed = installed_version(root)
    if installed is None:
        print(f"no mra-flow version installed in {root} ({VERSION_PATH} missing or not X.Y.Z)")
        return 1
    state = load_state(root)
    latest, reached = refresh(root, state, force=True)
    print(f"installed: {installed}")
    print(f"latest: {latest or 'unknown'}")
    if not reached:
        print("remote: unreachable, latest is the last one seen")
    if newer(latest, installed):
        ignored = parse(state.get("ignored")) is not None and not newer(latest, state.get("ignored"))
        print(f"status: update available{' (ignored)' if ignored else ''}")
    else:
        print("status: up to date" if latest else "status: unknown")
    return 0 if reached else 2


def ignore(root: pathlib.Path, version: str) -> int:
    if parse(version) is None:
        print(f"not a release version: {version} (expected X.Y.Z)", file=sys.stderr)
        return 1
    state = load_state(root)
    state["ignored"] = version
    save_state(root, state)
    print(f"mra-flow releases up to {version} will not be notified")
    return 0


def main(argv: list[str]) -> int:
    root = pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    if not (root / "mra-flow.toml").is_file():
        if argv:
            print(f"{root} is not an mra-flow orchestrator (no mra-flow.toml)", file=sys.stderr)
            return 1
        return 0
    if not argv:
        return hook(root)
    if argv == ["check"]:
        return check(root)
    if len(argv) == 2 and argv[0] == "ignore":
        return ignore(root, argv[1])
    print("usage: check-update.py [check | ignore <X.Y.Z>]", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
