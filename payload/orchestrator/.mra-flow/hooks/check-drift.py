#!/usr/bin/env python3
"""SessionStart hook and CLI: notice an empty repo registry, or new commits on a repo.

If mra-flow.toml exists but declares no [repos.*] yet, the orchestrator is not
really usable: the session is told to recommend `mra-repo add` for each code
repo, every session, until at least one is declared.

Otherwise, for each repo asks the remote (no fetch, no local writes other than
our own state file) for the SHA its default branch HEAD points to, and
compares it with the SHA last acknowledged for that repo. A repo seen for the
first time is recorded silently: there is nothing yet to compare it with. A
changed SHA means colleagues' commits may have landed, so openspec/specs/ may
be stale; the session is told to ask the user whether to run /mra-drift now,
later, or ignore those commits. The notice repeats on every session start and
/clear until the commits are acknowledged: by `/mra-drift` (run on every
capability) or by the user's "Ignore". A repo with `drift = false` in its
table (out of scope for this orchestrator's changes) is never checked.

  check-drift.py               SessionStart hook
  check-drift.py ack [<key>]   acknowledge the current remote HEAD of the given
                               repos (default: every checked repo)

It also keeps the project's one roadmap in shape (ADR-0012), every session
until fixed: changes but no roadmap -> recommend `/mra-roadmap --retro go-live`;
a second `docs/roadmap/*.md` -> merge it into go-live (or the oldest) with
`/mra-roadmap <initiative>`; the roadmap in person-days -> convert it the same way.

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


DEFAULT_INITIATIVE = "go-live"


def _created(path: pathlib.Path) -> str:
    found = re.search(r"^created:\s*(\S+)", path.read_text(encoding="utf-8", errors="replace"), re.M)
    return found.group(1) if found else "9999"


def roadmap_notices(root: pathlib.Path) -> list[tuple[str, str]]:
    """What to recommend about the project's one roadmap (ADR-0012)."""
    folder = root / "docs" / "roadmap"
    roadmaps = sorted(p for p in folder.glob("*.md") if not p.name.endswith("-effort.md")) \
        if folder.is_dir() else []
    if not roadmaps:
        changes = root / "openspec" / "changes"
        found = changes.is_dir() and any(p.is_dir() and p.name != "archive" for p in changes.iterdir())
        archive = changes / "archive"
        found |= archive.is_dir() and any(p.is_dir() for p in archive.iterdir())
        return [(f"changes but no roadmap — run /mra-roadmap --retro {DEFAULT_INITIATIVE}",
                 f"the project has OpenSpec changes but no roadmap: recommend `/mra-roadmap --retro "
                 f"{DEFAULT_INITIATIVE}`, which builds its one initiative with every change as a slice, "
                 f"estimates and actual hours ({DEFAULT_INITIATIVE} is the default name: the user may type "
                 "another name instead)")] if found else []
    # The one to keep: go-live when present, else the oldest by its front matter.
    keep = next((p for p in roadmaps if p.stem == DEFAULT_INITIATIVE), None) \
        or min(roadmaps, key=lambda p: (_created(p), p.name))
    notices = []
    for path in roadmaps:
        rel = path.relative_to(root).as_posix()
        if path != keep:
            notices.append((f"{rel}: merge it with /mra-roadmap {keep.stem}",
                            f"{rel} is a second roadmap: merge it with `/mra-roadmap {keep.stem}`"))
        elif re.search(r"\|\s*Estimate \(d\)\s*\|", path.read_text(encoding="utf-8", errors="replace")):
            notices.append((f"{rel} in days: convert it with /mra-roadmap {keep.stem}",
                            f"{rel} is in days: convert it with `/mra-roadmap {keep.stem}`"))
    return notices


def main(argv: list[str]) -> int:
    root = pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    if not (root / "mra-flow.toml").is_file():
        if argv:
            print(f"{root} is not an mra-flow orchestrator (no mra-flow.toml)", file=sys.stderr)
            return 1
        return 0
    if argv:
        if argv[0] != "ack":
            print("usage: check-drift.py [ack [<key> ...]]", file=sys.stderr)
            return 1
        return ack(root, argv[1:])
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
        sha = checked_sha(root, key, repo, state)
        if sha is None:
            continue
        previous = state.get(key)
        if previous is None:
            state[key] = sha  # first sight: the baseline, nothing to compare with yet
        elif previous != sha:
            changed.append(key)  # stays pending until acknowledged
    save_state(root, state)

    if not changed:
        return None
    repo_list = ", ".join(changed)
    keys = " ".join(changed)
    return (
        f"New commits on {repo_list} — check spec drift now, later or ignore?",
        f"New commits landed on the default branch of: {repo_list} (mra-flow SessionStart "
        "check-drift hook). openspec/specs/ may now be stale for capabilities those repos own. "
        "Before anything else in your first reply, ask the user with AskUserQuestion "
        '(header "Spec drift") what to do, and wait for the answer:\n'
        '- "Check now": follow `.claude/skills/mra-drift/SKILL.md` with no capability argument; '
        "at its end it acknowledges these commits. It is read-only, so other sessions are not "
        "disturbed.\n"
        '- "Later": do nothing; the question comes back on the next session start or /clear.\n'
        f'- "Ignore": run `python3 .mra-flow/hooks/check-drift.py ack {keys}`; only newer '
        "commits are notified again.\n"
        "Then go on with the user's request.",
    )


def checked_sha(root: pathlib.Path, key: str, repo: dict, state: dict) -> str | None:
    """The remote HEAD of a repo the hook checks, or None (out of scope, no clone, unreachable).
    A repo marked `drift = false` is also dropped from the state."""
    if repo.get("drift", True) is False:
        state.pop(key, None)
        return None
    path = root / repo.get("path", key)
    return remote_head_sha(path) if path.is_dir() else None


def ack(root: pathlib.Path, keys: list[str]) -> int:
    repos = load_repos(root)
    unknown = [k for k in keys if k not in repos]
    if unknown:
        print(f"unknown repo: {', '.join(unknown)} (see mra-flow.toml)", file=sys.stderr)
        return 1
    state = load_state(root)
    done, failed = [], []
    for key in keys or sorted(repos):
        sha = checked_sha(root, key, repos[key], state)
        if sha is None:
            if repos[key].get("drift", True) is not False:
                failed.append(key)
            continue
        state[key] = sha
        done.append(key)
    save_state(root, state)
    if done:
        print(f"acknowledged: {', '.join(done)}")
    if failed:
        print(f"not acknowledged (no clone or remote unreachable): {', '.join(failed)}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
