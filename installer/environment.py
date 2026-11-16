"""Prerequisite checks and the idempotent bootstrap of beads, OpenSpec and the registry."""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

from . import InstallError

PYTHON_MIN = (3, 11)
OPENSPEC_MIN = (1, 16, 0)     # below: refuse
OPENSPEC_TESTED = (1, 16, 0)  # above: warn
REQUIRED_TOOLS = ("git", "bd", "openspec")
REQUIRED_OPENSPEC_SKILLS = (
    "openspec-explore",
    "openspec-propose",
    "openspec-update-change",
    "openspec-sync-specs",
    "openspec-archive-change",
)

REGISTRY_PATH = "mra-flow.toml"
REGISTRY_SKELETON = """\
# mra-flow repo registry: one [repos.<key>] table per code repo of this orchestrator.
#
# The key is the repo's short name: task tag [<key>], beads label repo:<key>,
# worktree .worktrees/<change-id>/<key>. Add repos with the command below, which
# clones the repo, git-ignores it and appends its table here:
#
#   .mra-flow/bin/mra-repo add <key> <remote> --description "..." [--depends-on <key> ...]
#
# Example:
#
# [repos.be]
# path = "my-project-be"
# remote = "https://github.com/me/my-project-be.git"
# description = "Backend, owns the HTTP API"
# depends_on = []
#
# Optional: ui_paths = ["frontend/"] lists the paths of a repo's user interface;
# a change touching them gets browser checks from /mra-qa-ui (mra-repo add --ui-path).
"""


def _version(t: tuple[int, ...]) -> str:
    return ".".join(map(str, t))


def run(args: list[str], cwd: Path) -> str:
    try:
        done = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True)
    except FileNotFoundError as exc:
        raise InstallError(f"{args[0]} not found on PATH") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise InstallError(f"`{' '.join(args)}` failed: {detail}") from exc
    return done.stdout


def check_python() -> None:
    if sys.version_info < PYTHON_MIN:
        raise InstallError(f"mra-flow needs python3 >= {_version(PYTHON_MIN)}")


def check_target(root: Path) -> None:
    if not root.is_dir():
        raise InstallError(f"{root} is not a directory")
    try:
        top = run(["git", "rev-parse", "--show-toplevel"], root).strip()
    except InstallError:
        raise InstallError(f"{root} is not a git repository") from None
    if Path(top).resolve() != root.resolve():
        raise InstallError(f"{root} is inside the git repo {top}; pass the repo root")


def check_tools() -> None:
    missing = [t for t in REQUIRED_TOOLS if shutil.which(t) is None]
    if missing:
        raise InstallError("missing on PATH: " + ", ".join(missing))


def check_openspec_version(cwd: Path) -> list[str]:
    out = run(["openspec", "--version"], cwd)
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", out)
    if not match:
        raise InstallError(f"cannot read the OpenSpec version from {out.strip()!r}")
    found = tuple(int(g) for g in match.groups())
    if found < OPENSPEC_MIN:
        raise InstallError(f"OpenSpec {_version(found)} is older than the required "
                           f"{_version(OPENSPEC_MIN)}; upgrade it first")
    if found > OPENSPEC_TESTED:
        return [f"OpenSpec {_version(found)} is newer than the tested "
                f"{_version(OPENSPEC_TESTED)}; if an mra-* skill misbehaves, "
                "update mra-flow or report it"]
    return []


def check_openspec_skills(root: Path) -> None:
    missing = [n for n in REQUIRED_OPENSPEC_SKILLS
               if not (root / ".claude" / "skills" / n / "SKILL.md").is_file()]
    if missing:
        raise InstallError(
            "OpenSpec skills missing: " + ", ".join(missing)
            + ". Enable those workflows in your OpenSpec profile (`openspec config profile`),"
            " then run `openspec update` and re-run the installer")


def ensure_openspec(root: Path) -> list[str]:
    notes = []
    if not (root / "openspec").exists():
        run(["openspec", "init", "--tools", "claude", "."], root)
        notes.append("ran openspec init")
    config = root / "openspec" / "config.yaml"
    text = config.read_text(encoding="utf-8") if config.exists() else ""
    if re.search(r"^schema:\s*mra-flow\s*$", text, re.MULTILINE):
        return notes
    if re.search(r"^schema:.*$", text, re.MULTILINE):
        text = re.sub(r"^schema:.*$", "schema: mra-flow", text, count=1, flags=re.MULTILINE)
    else:
        text = "schema: mra-flow\n" + text
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(text, encoding="utf-8")
    notes.append("set schema: mra-flow in openspec/config.yaml")
    return notes


def _head(root: Path) -> str | None:
    try:
        return run(["git", "rev-parse", "--short", "HEAD"], root).strip()
    except InstallError:
        return None


def ensure_beads(root: Path) -> list[str]:
    notes = []
    if not (root / ".beads").exists():
        before = _head(root)
        run(["bd", "init", "--skip-agents"], root)
        run(["bd", "setup", "claude"], root)
        notes.append("ran bd init --skip-agents and bd setup claude")
        after = _head(root)
        if after and after != before:
            notes.append(f"bd init created commit {after}")
    run(["git", "config", "beads.role", "maintainer"], root)
    return notes


def ensure_registry(root: Path) -> bool:
    path = root / REGISTRY_PATH
    if path.exists():
        return False
    path.write_text(REGISTRY_SKELETON, encoding="utf-8")
    return True
