#!/usr/bin/env python3
"""SessionStart hook: notice an empty repo registry, or new commits on a repo.

If mra-flow.toml exists but declares no [repos.*] yet, the orchestrator is not
really usable: the session is told to recommend `mra-repo add` for each code
repo, every session, until at least one is declared.

Otherwise, for each repo asks the remote (no fetch, no local writes other than
our own state file) for the SHA its default branch HEAD points to, and
compares it with the SHA last seen for that repo. A repo seen for the first
time is recorded silently: there is nothing yet to compare it with. A changed
SHA means colleagues' commits may have landed since the last check, so
openspec/specs/ may be stale; the session is told to recommend /mra-drift,
never to run it. A repo with `drift = false` in its table (out of scope for
this orchestrator's changes) is never checked.

It also keeps the project's one roadmap in shape (ADR-0012), every session
until fixed: changes but no roadmap -> recommend `/mra-roadmap --retro`;
another `docs/roadmap/*.md` -> merge it with `/mra-roadmap <project>`; the
project's roadmap in person-days -> convert it the same way.

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


def emit(system_message: str, context: str) -> None:
    json.dump(
        {
            "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context},
            "systemMessage": system_message,
        },
        sys.stdout,
    )


def roadmap_notices(root: pathlib.Path) -> list[tuple[str, str]]:
    """What to recommend about the project's one roadmap, <root name>.md."""
    project = root.name
    folder = root / "docs" / "roadmap"
    roadmaps = sorted(p for p in folder.glob("*.md") if not p.name.endswith("-effort.md")) \
        if folder.is_dir() else []
    if not roadmaps:
        changes = root / "openspec" / "changes"
        found = changes.is_dir() and any(p.is_dir() and p.name != "archive" for p in changes.iterdir())
        archive = changes / "archive"
        found |= archive.is_dir() and any(p.is_dir() for p in archive.iterdir())
        return [("changes but no roadmap — run /mra-roadmap --retro",
                 "the project has OpenSpec changes but no roadmap: recommend `/mra-roadmap --retro`, which "
                 "builds its one initiative with every change as a slice, estimates and actual hours")] \
            if found else []
    notices = []
    for path in roadmaps:
        rel = path.relative_to(root).as_posix()
        if path.stem != project:
            notices.append((f"{rel}: merge it with /mra-roadmap {project}",
                            f"{rel} is not the project's one roadmap: merge it with `/mra-roadmap {project}`"))
        elif re.search(r"\|\s*Estimate \(d\)\s*\|", path.read_text(encoding="utf-8", errors="replace")):
            notices.append((f"{rel} in days: convert it with /mra-roadmap {project}",
                            f"{rel} is in days: convert it with `/mra-roadmap {project}`"))
    return notices


def main() -> int:
    root = pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    if not (root / "mra-flow.toml").is_file():
        return 0
    notices = [(short, "mra-flow SessionStart check-drift hook, roadmap check: " + long + ". Tell the user "
                "this at the start of the conversation and recommend the command; do not run it yourself.")
               for short, long in roadmap_notices(root)]
    repo_notice = drift_notice(root)
    if repo_notice:
        notices.append(repo_notice)
    if notices:
        emit(" · ".join(n[0] for n in notices), "\n\n".join(n[1] for n in notices))
    return 0


def drift_notice(root: pathlib.Path) -> tuple[str, str] | None:
    repos = load_repos(root)
    if not repos:
        return (
            "mra-flow.toml has no repos declared yet — run mra-repo add",
            "mra-flow.toml declares no [repos.*] yet (mra-flow SessionStart check-drift hook). "
            "Tell the user this at the start of the conversation and recommend "
            '`.mra-flow/bin/mra-repo add <key> <remote> --description "..."` for each code repo; '
            "do not run it yourself.",
        )
    state = load_state(root)
    changed = []
    for key, repo in sorted(repos.items()):
        if repo.get("drift", True) is False:
            state.pop(key, None)
            continue
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
        return None
    repo_list = ", ".join(changed)
    return (
        f"New commits on {repo_list} since the last check — consider /mra-drift",
        f"New commits landed on the default branch of: {repo_list} (mra-flow SessionStart "
        "check-drift hook). openspec/specs/ may now be stale for capabilities those repos own. "
        "Tell the user this at the start of the conversation and recommend running /mra-drift "
        "to check; do not run it yourself.",
    )


if __name__ == "__main__":
    sys.exit(main())
