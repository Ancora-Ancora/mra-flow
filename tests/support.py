"""Helpers: fake orchestrators, package copies and an environment with fake bd/openspec."""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FAKES = REPO_ROOT / "tests" / "fakes" / "bin"
PACKAGE_PARTS = ("install.sh", "install.py", "installer", "payload", "VERSION")


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True,
                          capture_output=True, text=True).stdout.strip()


def make_package(tmp: Path) -> Path:
    pkg = tmp / "package"
    pkg.mkdir()
    for part in PACKAGE_PARTS:
        src = REPO_ROOT / part
        if src.is_dir():
            shutil.copytree(src, pkg / part, ignore=shutil.ignore_patterns("__pycache__"))
        elif src.exists():
            shutil.copy2(src, pkg / part)
    # Pin the version so tests do not depend on the release being prepared.
    (pkg / "VERSION").write_text("0.1.0\n")
    return pkg


def make_orchestrator(tmp: Path, name: str = "orch") -> Path:
    root = tmp / name
    root.mkdir()
    git(root, "init", "--quiet", "-b", "main")
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.com")
    git(root, "commit", "--quiet", "--allow-empty", "-m", "init")
    return root


def make_bare_remote(tmp: Path, name: str) -> Path:
    """A bare repo with one commit, usable as a clone remote."""
    work = make_orchestrator(tmp, f"{name}-work")
    bare = tmp / f"{name}.git"
    git(tmp, "clone", "--quiet", "--bare", str(work), str(bare))
    return bare


def fake_env(tmp: Path, openspec_version: str = "1.16.0", **extra: str) -> dict[str, str]:
    env = dict(os.environ)
    env["PATH"] = f"{FAKES}{os.pathsep}{env['PATH']}"
    env["FAKE_LOG"] = str(tmp / "calls.log")
    env["FAKE_OPENSPEC_VERSION"] = openspec_version
    # never touch the real user config: Claude Code dir, git global config, XDG
    home = tmp / "home"
    home.mkdir(exist_ok=True)
    env["HOME"] = str(home)
    env["CLAUDE_CONFIG_DIR"] = str(home / ".claude")
    env["XDG_CONFIG_HOME"] = str(home / ".config")
    env["GIT_CONFIG_GLOBAL"] = str(home / ".gitconfig")
    env.update(extra)
    return env


def calls(tmp: Path) -> list[str]:
    log = tmp / "calls.log"
    return log.read_text().splitlines() if log.exists() else []


def snapshot(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file() and ".git" not in p.relative_to(root).parts
    }


def run_install(pkg: Path, target, env: dict[str, str]) -> subprocess.CompletedProcess:
    """target: an orchestrator Path, or "--user"."""
    return subprocess.run([sys.executable, str(pkg / "install.py"), str(target)],
                          env=env, capture_output=True, text=True)


class TmpTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name).resolve()
        self.addCleanup(self._tmp.cleanup)
