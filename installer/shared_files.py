"""Minimal, idempotent edits of the files the package shares with their owner.

Each function returns True when it changed the file. None of them rewrites
content it does not own: they only add what is missing.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from . import InstallError

# Orchestrator layer.
IMPORT_LINE = "@.mra-flow/CLAUDE.md"
REQUIRED_PLUGINS = (
    "superpowers@claude-plugins-official",
    "mattpocock-skills@claude-plugins-official",
)
GITIGNORE_LINES = (".worktrees/", "handoff/", ".beads/issues.jsonl", ".mra-flow/drift-state.json",
                   ".mra-flow/update-state.json")
DRIFT_HOOK_SCRIPT = ".mra-flow/hooks/check-drift.py"
UPDATE_HOOK_SCRIPT = ".mra-flow/hooks/check-update.py"

# User layer (paths relative to the Claude Code config dir).
USER_IMPORT_LINE = "@mra-flow/CLAUDE.md"
HOOK_SCRIPT = "mra-flow/hooks/load-handoff.py"


def hook_entry(claude_dir: Path) -> dict:
    command = f'python3 "{claude_dir / HOOK_SCRIPT}"'
    return {
        "matcher": "startup|clear|compact",
        "hooks": [{"type": "command", "command": command, "timeout": 10}],
    }


# The orchestrator checks run on a new session and on /clear, not on resume: a
# resumed conversation already got (and answered) their question.
CHECK_HOOK_MATCHER = "startup|clear"


def drift_hook_entry(root: Path) -> dict:
    command = f'python3 "{root / DRIFT_HOOK_SCRIPT}"'
    return {
        "matcher": CHECK_HOOK_MATCHER,
        "hooks": [{"type": "command", "command": command, "timeout": 15}],
    }


def update_hook_entry(root: Path) -> dict:
    command = f'python3 "{root / UPDATE_HOOK_SCRIPT}"'
    return {
        "matcher": CHECK_HOOK_MATCHER,
        "hooks": [{"type": "command", "command": command, "timeout": 15}],
    }


def ensure_import(claude_md: Path, line: str) -> bool:
    if not claude_md.exists():
        claude_md.parent.mkdir(parents=True, exist_ok=True)
        claude_md.write_text(line + "\n", encoding="utf-8")
        return True
    text = claude_md.read_text(encoding="utf-8")
    if any(x.strip() == line for x in text.splitlines()):
        return False
    if text and not text.endswith("\n"):
        text += "\n"
    claude_md.write_text(text + "\n" + line + "\n", encoding="utf-8")
    return True


def ensure_claude_import(root: Path) -> bool:
    return ensure_import(root / "CLAUDE.md", IMPORT_LINE)


def merge_settings(path: Path, *, hook: dict | None = None,
                   plugins: Iterable[str] = ()) -> bool:
    """Add `hook` to hooks.SessionStart (replacing any entry running HOOK_SCRIPT)
    and enable `plugins` unless the user set them explicitly."""
    original = path.read_text(encoding="utf-8") if path.exists() else None
    try:
        settings = json.loads(original) if original is not None else {}
    except ValueError as exc:
        raise InstallError(f"{path} is not valid JSON ({exc}); fix it and re-run") from exc
    if not isinstance(settings, dict):
        raise InstallError(f"{path} must hold a JSON object")

    if hook is not None:
        session_start = settings.setdefault("hooks", {}).setdefault("SessionStart", [])
        marker = _hook_marker(hook)
        ours = [i for i, e in enumerate(session_start) if _runs_hook_script(e, marker)]
        if ours:
            session_start[:] = [e for i, e in enumerate(session_start) if i not in ours[1:]]
            session_start[ours[0]] = hook
        else:
            session_start.append(hook)

    if plugins:
        enabled = settings.setdefault("enabledPlugins", {})
        for name in plugins:
            if name not in enabled and _same_plugin_enabled(enabled, name):
                continue  # another copy of this plugin (e.g. a vendored one) is in use
            enabled.setdefault(name, True)  # an explicit false from the user wins

    if original is not None and json.loads(original) == settings:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    return True


def _same_plugin_enabled(enabled: dict, name: str) -> bool:
    """True if a plugin with the same name from another marketplace is enabled,
    e.g. superpowers@local-plugins when name is superpowers@claude-plugins-official."""
    base = name.split("@", 1)[0]
    return any(other.split("@", 1)[0] == base and value is True
               for other, value in enabled.items() if other != name)


def _hook_marker(hook: dict) -> str:
    """The script filename a hook runs, used to recognize it across installs that moved
    the Claude Code config dir or the orchestrator root (the absolute path changes,
    the filename does not)."""
    command = hook["hooks"][0]["command"]
    return Path(command.split('"')[1]).name


def _runs_hook_script(entry: object, marker: str) -> bool:
    if not isinstance(entry, dict):
        return False
    return any(marker in str(h.get("command", ""))
               for h in entry.get("hooks", []) if isinstance(h, dict))


def ensure_lines(path: Path, lines: Iterable[str]) -> bool:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    present = {x.strip() for x in text.splitlines()}
    missing = [x for x in lines if x not in present]
    if not missing:
        return False
    if text and not text.endswith("\n"):
        text += "\n"
    header = "" if "# mra-flow" in present else ("\n" if text else "") + "# mra-flow\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + header + "\n".join(missing) + "\n", encoding="utf-8")
    return True


def ensure_gitignore(root: Path, lines: Iterable[str] = GITIGNORE_LINES) -> bool:
    return ensure_lines(root / ".gitignore", lines)

