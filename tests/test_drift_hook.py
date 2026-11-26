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

    def test_empty_registry_recommends_mra_repo_add(self):
        self.toml("# mra-flow repo registry: no [repos.*] declared yet\n")
        done = self.run_hook()
        payload = json.loads(done.stdout)
        self.assertIn("mra-repo add", payload["systemMessage"])
        self.assertIn("mra-repo add", payload["hookSpecificOutput"]["additionalContext"])
        self.assertFalse((self.orch / ".mra-flow/drift-state.json").exists())

        # repeats every session, unlike the drift notice, which fires once per change
        again = self.run_hook()
        self.assertIn("mra-repo add", again.stdout)

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

    def test_repo_with_drift_false_is_never_reported(self):
        self.toml('[repos.be]\npath = "be"\nremote = "x"\ndescription = "d"\ndrift = false\n')
        self.run_hook()
        self.push_new_commit()

        done = self.run_hook()
        self.assertEqual(done.stdout, "")
        self.assertNotIn("be", self.state())

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


class RoadmapNoticeTest(TmpTestCase):
    """The same SessionStart hook keeps the project's one roadmap in shape (ADR-0012)."""

    def setUp(self):
        super().setUp()
        self.env = fake_env(self.tmp)
        self.orch = self.tmp / "shop"
        self.orch.mkdir()
        git(self.orch, "init", "--quiet")
        (self.orch / "mra-flow.toml").write_text('[repos.be]\npath = "be"\nremote = "x"\ndescription = "d"\n')

    def run_hook(self) -> str:
        env = dict(self.env, CLAUDE_PROJECT_DIR=str(self.orch))
        done = subprocess.run([sys.executable, str(HOOK)], cwd=self.orch, env=env,
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        return done.stdout

    def roadmap(self, name: str, unit: str = "h") -> None:
        folder = self.orch / "docs/roadmap"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{name}.md").write_text(f"## Slices\n\n| # | Estimate ({unit}) |\n")

    def test_no_changes_no_notice(self):
        self.assertEqual(self.run_hook(), "")

    def test_changes_without_roadmap_recommend_retro_every_session(self):
        (self.orch / "openspec/changes/archive/2026-01-01-add-a").mkdir(parents=True)
        out = json.loads(self.run_hook())
        self.assertIn("/mra-roadmap --retro", out["systemMessage"])
        self.assertIn("/mra-roadmap --retro", out["hookSpecificOutput"]["additionalContext"])
        self.assertIn("/mra-roadmap --retro", self.run_hook())  # until the roadmap exists

    def test_in_flight_change_counts_too(self):
        (self.orch / "openspec/changes/add-a").mkdir(parents=True)
        self.assertIn("/mra-roadmap --retro", self.run_hook())

    def test_project_roadmap_in_hours_is_quiet(self):
        (self.orch / "openspec/changes/add-a").mkdir(parents=True)
        self.roadmap("shop")
        (self.orch / "docs/roadmap/shop-effort.md").write_text("generated\n")
        self.assertEqual(self.run_hook(), "")

    def test_other_roadmap_is_to_be_merged(self):
        self.roadmap("shop")
        self.roadmap("go-live")
        out = self.run_hook()
        self.assertIn("docs/roadmap/go-live.md", out)
        self.assertIn("/mra-roadmap shop", out)

    def test_roadmap_in_days_is_to_be_converted(self):
        self.roadmap("shop", unit="d")
        out = self.run_hook()
        self.assertIn("in days", out)
        self.assertIn("/mra-roadmap shop", out)
