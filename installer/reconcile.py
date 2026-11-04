"""Checksum manifest and the per-file decision of what an install or update does.

`payload/<rel>` is installed at `<orchestrator>/<rel>`. The manifest records the
sha256 of each file as installed, so a later update can tell a file the user
edited (left alone) from one still as installed (safe to replace).
"""
from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from . import InstallError

ORCHESTRATOR_STATE = ".mra-flow"  # manifest and version, relative to the target root
USER_STATE = "mra-flow"           # same, relative to the Claude Code config dir
MANIFEST_PATH = f"{ORCHESTRATOR_STATE}/manifest"
VERSION_PATH = f"{ORCHESTRATOR_STATE}/version"

# Action kinds.
COPY = "copy"                        # write the payload file
UNCHANGED = "unchanged"              # already as in the payload
ADOPT = "adopt"                      # identical to the payload, start tracking it
CONFLICT = "conflict"                # unmanaged file in an owned path: refuse
SKIP_LOCAL_EDIT = "skip-local-edit"  # user edited it: leave alone
SKIP_DELETED = "skip-deleted"        # user deleted it: leave deleted
DELETE = "delete"                    # dropped from the payload, unedited: remove
KEEP_ORPHAN = "keep-orphan"          # dropped from the payload, but edited: keep
FORGET = "forget"                    # dropped from the payload, already gone

LEFT_ALONE = (SKIP_LOCAL_EDIT, SKIP_DELETED, KEEP_ORPHAN)


@dataclass
class Manifest:
    version: str
    files: dict[str, str]


@dataclass(frozen=True)
class Action:
    kind: str
    path: str


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(root: Path, state: str = ORCHESTRATOR_STATE) -> Manifest | None:
    path = root / state / "manifest"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Manifest(version=str(data["version"]), files=dict(data["files"]))
    except (ValueError, KeyError, TypeError) as exc:
        raise InstallError(f"{path} is unreadable ({exc}); restore or delete it") from exc


def save_manifest(root: Path, manifest: Manifest, state: str = ORCHESTRATOR_STATE) -> None:
    path = root / state / "manifest"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"version": manifest.version, "files": dict(sorted(manifest.files.items()))}
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (root / state / "version").write_text(manifest.version + "\n", encoding="utf-8")


def payload_files(payload: Path) -> dict[str, str]:
    """Map each payload file's posix relative path to its sha256."""
    return {
        p.relative_to(payload).as_posix(): sha256_file(p)
        for p in sorted(payload.rglob("*"))
        if p.is_file()
    }


def plan(payload: Path, dest: Path, manifest: Manifest | None) -> list[Action]:
    shipped = payload_files(payload)
    known = manifest.files if manifest else {}
    actions = []
    for rel in sorted(set(shipped) | set(known)):
        target = dest / rel
        p, m = shipped.get(rel), known.get(rel)
        d = sha256_file(target) if target.is_file() else None
        actions.append(Action(_decide(p, d, m), rel))
    return actions


def _decide(p: str | None, d: str | None, m: str | None) -> str:
    if p is None:  # no longer shipped
        if d is None:
            return FORGET
        return DELETE if d == m else KEEP_ORPHAN
    if d is None:
        return SKIP_DELETED if m is not None else COPY
    if d == p:
        return UNCHANGED if m == p else ADOPT
    if m is None:
        return CONFLICT
    return COPY if d == m else SKIP_LOCAL_EDIT


def apply(actions: list[Action], payload: Path, dest: Path, version: str,
          old: Manifest | None) -> Manifest:
    if any(a.kind == CONFLICT for a in actions):
        raise InstallError("refusing to apply a plan with conflicts")
    known = old.files if old else {}
    files: dict[str, str] = {}
    for a in actions:
        src, target = payload / a.path, dest / a.path
        if a.kind == COPY:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
            files[a.path] = sha256_file(target)
        elif a.kind in (UNCHANGED, ADOPT):
            files[a.path] = sha256_file(src)
        elif a.kind in (SKIP_LOCAL_EDIT, SKIP_DELETED):
            files[a.path] = known[a.path]  # keep the old sum: stays flagged
        elif a.kind == DELETE:
            target.unlink()
            _prune_empty_dirs(target.parent, dest)
    return Manifest(version=version, files=files)


def _prune_empty_dirs(path: Path, stop: Path) -> None:
    while path != stop and path.is_dir() and not any(path.iterdir()):
        path.rmdir()
        path = path.parent
