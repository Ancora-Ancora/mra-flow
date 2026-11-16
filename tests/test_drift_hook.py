import json
import subprocess
import sys
from pathlib import Path

from tests.support import REPO_ROOT, TmpTestCase, fake_env, git, make_bare_remote

HOOK = REPO_ROOT / "payload/orchestrator/.mra-flow/hooks/check-drift.py"


class DriftHookTest(TmpTestCase):
    def setUp(self):
        super().setUp()
        self.env = fake_env(self.tmp)
        self.orch = self.tmp / "orch"
        self.orch.mkdir()
        git(self.orch, "init", "--quiet")
        self.remote = make_bare_remote(self.tmp, "be")
        git(self.orch, "clone", "--quiet", str(self.remote), "be")

    def toml(self, text: str) -> None:
        (self.orch / "mra-flow.toml").write_text(text)

    def run_hook(self) -> subprocess.CompletedProcess:
        env = dict(self.env, CLAUDE_PROJECT_DIR=str(self.orch))
        done = subprocess.run([sys.executable, str(HOOK)], cwd=self.orch, env=env,
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        return done

    def push_new_commit(self) -> None:
        work = self.tmp / "be-work"
        git(work, "commit", "--quiet", "--allow-empty", "-m", "more work")
        git(work, "push", "--quiet", str(self.remote), "HEAD:main")

    def state(self) -> dict:
        return json.loads((self.orch / ".mra-flow/drift-state.json").read_text())

    def test_no_registry_does_nothing(self):
        done = self.run_hook()
        self.assertEqual(done.stdout, "")
        self.assertFalse((self.orch / ".mra-flow").exists())

    def test_first_run_is_silent_and_records_baseline(self):
        self.toml('[repos.be]\npath = "be"\nremote = "x"\ndescription = "d"\n')
        done = self.run_hook()
        self.assertEqual(done.stdout, "")
        self.assertIn("be", self.state())

    def test_unchanged_remote_stays_silent(self):
        self.toml('[repos.be]\npath = "be"\nremote = "x"\ndescription = "d"\n')
        self.run_hook()
        done = self.run_hook()
        self.assertEqual(done.stdout, "")

    def test_new_commit_is_reported_once(self):
        self.toml('[repos.be]\npath = "be"\nremote = "x"\ndescription = "d"\n')
        self.run_hook()
        self.push_new_commit()

        done = self.run_hook()
        payload = json.loads(done.stdout)
        self.assertIn("be", payload["systemMessage"])
        self.assertIn("mra-drift", payload["hookSpecificOutput"]["additionalContext"])

        quiet = self.run_hook()
        self.assertEqual(quiet.stdout, "")

    def test_missing_clone_is_skipped(self):
        self.toml('[repos.fe]\npath = "fe"\nremote = "x"\ndescription = "d"\n')
        done = self.run_hook()
        self.assertEqual(done.stdout, "")
        self.assertNotIn("fe", self.state())

    def test_outside_an_orchestrator_does_nothing(self):
        plain = self.tmp / "plain"
        plain.mkdir()
        env = dict(self.env, CLAUDE_PROJECT_DIR=str(plain))
        done = subprocess.run([sys.executable, str(HOOK)], cwd=plain, env=env,
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stdout, "")
