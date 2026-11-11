#!/usr/bin/env python3
"""SessionStart hook: load the latest unread handoff into the new session.

Looks at the newest handoff/ho-<YYYYMMDD-HHMMSS>.md file (by name, which sorts
chronologically). If its frontmatter says `read: false`, the file content is
injected as additionalContext and the file is marked `read: true` with a
`read_at` timestamp. If the newest file is already read, or there is none,
the hook prints nothing. Older files are never loaded.

First, in a git repo, it adds `handoff/` to the repo's info/exclude (the common
git dir, so worktrees share it). Unlike the global excludes file, that file
lives in the project, so it survives where the user's git config does not
(e.g. a rebuilt dev container).
"""
import datetime
import json
import os
import pathlib
import re
import subprocess
import sys

READ_FALSE = re.compile(r"^read:\s*false\s*$", re.MULTILINE)
EXCLUDE_LINE = "handoff/"


def ignore_handoff_dir(root: pathlib.Path) -> None:
    """Add EXCLUDE_LINE to the repo's info/exclude; never fail the session."""
    try:
        done = subprocess.run(["git", "rev-parse", "--git-common-dir"],
                              cwd=root, capture_output=True, text=True, timeout=5)
        if done.returncode != 0:
            return
        exclude = root / done.stdout.strip() / "info" / "exclude"  # path may be relative
        text = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
        if EXCLUDE_LINE in text.splitlines():
            return
        if text and not text.endswith("\n"):
            text += "\n"
        exclude.parent.mkdir(parents=True, exist_ok=True)
        exclude.write_text(text + EXCLUDE_LINE + "\n", encoding="utf-8")
    except (OSError, subprocess.SubprocessError):
        pass


def main() -> int:
    root = pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    ignore_handoff_dir(root)
    files = sorted((root / "handoff").glob("ho-*.md"))
    if not files:
        return 0
    latest = files[-1]
    text = latest.read_text(encoding="utf-8")

    # The flag must live in the leading frontmatter block.
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match or not READ_FALSE.search(match.group(1)):
        return 0

    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    frontmatter = READ_FALSE.sub(f"read: true\nread_at: {now}", match.group(1), count=1)
    latest.write_text(f"---\n{frontmatter}\n---\n" + text[match.end():], encoding="utf-8")

    rel = latest.relative_to(root)
    context = (
        f"Handoff from the previous session ({rel}), loaded once and now marked read. "
        "Continue from it; follow its suggested skills.\n\n" + text
    )
    json.dump(
        {
            "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context},
            "systemMessage": f"Loaded handoff {rel}",
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
