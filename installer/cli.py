"""install.py entry: check, refuse on conflicts before writing, bootstrap, apply, report.

Two layers: `install.py <orchestrator-dir>` installs the OpenSpec workflow into an
orchestrator; `install.py --user` installs the personal harness conventions
(handoff hook and rules, language, memory) into the Claude Code config dir.
"""
from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path

from . import InstallError
from . import environment as env
from . import reconcile as rc
from . import shared_files as sf

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
USAGE = "usage: install.py <orchestrator-dir> | install.py --user"


def claude_config_dir() -> Path:
    configured = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(configured).expanduser() if configured else Path.home() / ".claude"


def active_change_warnings(root: Path) -> list[str]:
    warnings = []
    worktrees = root / ".worktrees"
    if worktrees.is_dir():
        warnings += [f"worktree in flight: .worktrees/{p.name}" for p in sorted(worktrees.iterdir())]
    changes = root / "openspec" / "changes"
    if changes.is_dir():
        warnings += [f"OpenSpec change in flight: {p.name}" for p in sorted(changes.iterdir())
                     if p.is_dir() and p.name != "archive"]
    if warnings:
        warnings.append("updated skills apply to these changes from now on")
    return warnings


def _version(package: Path) -> str:
    return (package / "VERSION").read_text(encoding="utf-8").strip()


def _plan_or_refuse(payload: Path, target: Path, state: str):
    manifest = rc.load_manifest(target, state)
    actions = rc.plan(payload, target, manifest)
    conflicts = [a.path for a in actions if a.kind == rc.CONFLICT]
    if conflicts:
        print(f"Refusing: unmanaged files in mra-flow paths under {target}:")
        for path in conflicts:
            print(f"  {path}")
        print("Move or delete them, then re-run. Nothing was changed.")
    return manifest, actions, bool(conflicts)


def install_orchestrator(root: Path, package: Path = PACKAGE_ROOT) -> int:
    payload, version = package / "payload" / "orchestrator", _version(package)

    env.check_python()
    env.check_target(root)
    env.check_tools()
    warnings = env.check_openspec_version(root)

    manifest, actions, refused = _plan_or_refuse(payload, root, rc.ORCHESTRATOR_STATE)
    if refused:
        return 1
    if manifest is not None:
        warnings += active_change_warnings(root)
    if rc.load_manifest(claude_config_dir(), rc.USER_STATE) is None:
        warnings.append("personal conventions (handoff, language, memory) are not installed: "
                        "run install.sh --user")

    notes = env.ensure_openspec(root)
    env.check_openspec_skills(root)
    notes += env.ensure_beads(root)

    rc.save_manifest(root, rc.apply(actions, payload, root, version, manifest))

    if sf.ensure_claude_import(root):
        notes.append(f"added {sf.IMPORT_LINE} to CLAUDE.md")
    if sf.merge_settings(root / ".claude" / "settings.json", plugins=sf.REQUIRED_PLUGINS):
        notes.append("enabled the required plugins in .claude/settings.json")
    if sf.ensure_gitignore(root):
        notes.append("updated .gitignore")
    if env.ensure_registry(root):
        notes.append(f"created {env.REGISTRY_PATH}")

    _report(root, version, manifest, actions, notes, warnings, [
        '.mra-flow/bin/mra-repo add <key> <remote> --description "..." [--depends-on <key> ...]',
        "review the changes with git status, then commit them",
    ])
    return 0


def install_user(claude_dir: Path, package: Path = PACKAGE_ROOT) -> int:
    payload, version = package / "payload" / "user", _version(package)
    env.check_python()

    manifest, actions, refused = _plan_or_refuse(payload, claude_dir, rc.USER_STATE)
    if refused:
        return 1
    claude_dir.mkdir(parents=True, exist_ok=True)
    rc.save_manifest(claude_dir, rc.apply(actions, payload, claude_dir, version, manifest),
                     rc.USER_STATE)

    notes = []
    if sf.ensure_import(claude_dir / "CLAUDE.md", sf.USER_IMPORT_LINE):
        notes.append(f"added {sf.USER_IMPORT_LINE} to {claude_dir / 'CLAUDE.md'}")
    if sf.merge_settings(claude_dir / "settings.json", hook=sf.hook_entry(claude_dir)):
        notes.append(f"added the handoff hook to {claude_dir / 'settings.json'}")
    excludes = sf.global_excludes_file()
    if sf.ensure_lines(excludes, sf.GLOBAL_EXCLUDES):
        notes.append(f"git-ignored handoff/ globally in {excludes}")

    _report(claude_dir, version, manifest, actions, notes, [], [
        "start a new Claude Code session to load the conventions",
    ])
    return 0


def _report(target, version, old, actions, notes, warnings, next_steps) -> None:
    verb = "installed" if old is None else f"updated from {old.version}"
    print(f"mra-flow {version} {verb} in {target}")
    counts = Counter(a.kind for a in actions)
    print("files: " + ", ".join(f"{k} {n}" for k, n in sorted(counts.items())))
    for a in actions:
        if a.kind in rc.LEFT_ALONE:
            print(f"  left alone ({a.kind}): {a.path}")
    for n in notes:
        print(f"note: {n}")
    for w in warnings:
        print(f"warning: {w}")
    print("next:")
    for step in next_steps:
        print(f"  {step}")


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] in ("-h", "--help"):
        print(USAGE, file=sys.stderr)
        return 1
    try:
        if argv[0] == "--user":
            return install_user(claude_config_dir())
        return install_orchestrator(Path(argv[0]).resolve())
    except InstallError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
