import subprocess
import sys
from pathlib import Path

from tests.support import REPO_ROOT, TmpTestCase, fake_env, git

HOOK = REPO_ROOT / "payload/user/mra-flow/hooks/load-handoff.py"


class HandoffHookExcludeTest(TmpTestCase):
    def setUp(self):
        super().setUp()
        self.env = fake_env(self.tmp)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "--quiet")

    def hook(self, project: Path):
        env = dict(self.env, CLAUDE_PROJECT_DIR=str(project))
        done = subprocess.run([sys.executable, str(HOOK)], cwd=project, env=env,
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        return done

    def exclude_lines(self) -> list[str]:
        return (self.repo / ".git/info/exclude").read_text().splitlines()

    def test_ignores_handoff_dir_once(self):
        self.hook(self.repo)
        self.hook(self.repo)
        self.assertEqual(self.exclude_lines().count("handoff/"), 1)
        (self.repo / "handoff").mkdir()
        (self.repo / "handoff/ho-20260101-000000.md").write_text("---\nread: true\n---\n")
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")

    def test_worktree_writes_the_common_git_dir(self):
        git(self.repo, "commit", "--quiet", "--allow-empty", "-m", "init")
        tree = self.tmp / "tree"
        git(self.repo, "worktree", "add", "--quiet", str(tree))
        self.hook(tree)
        self.assertIn("handoff/", self.exclude_lines())

    def test_outside_a_repo_does_nothing(self):
        plain = self.tmp / "plain"
        plain.mkdir()
        done = self.hook(plain)
        self.assertEqual(done.stdout, "")
        self.assertFalse((plain / ".git").exists())

    def test_still_loads_an_unread_handoff(self):
        (self.repo / "handoff").mkdir()
        (self.repo / "handoff/ho-20260101-000000.md").write_text("---\nread: false\n---\nhi\n")
        self.assertIn("Loaded handoff", self.hook(self.repo).stdout)
        self.assertIn("handoff/", self.exclude_lines())
