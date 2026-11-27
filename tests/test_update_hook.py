import json
import shutil
import subprocess
import sys
import time

from tests.support import REPO_ROOT, TmpTestCase, fake_env, git, make_bare_remote

HOOK = REPO_ROOT / "payload/orchestrator/.mra-flow/hooks/check-update.py"


class UpdateHookTest(TmpTestCase):
    def setUp(self):
        super().setUp()
        self.env = fake_env(self.tmp)
        self.orch = self.tmp / "orch"
        self.orch.mkdir()
        (self.orch / "mra-flow.toml").write_text("")
        self.set_installed("0.1.20")
        self.remote = make_bare_remote(self.tmp, "rel")

    def set_installed(self, version):
        (self.orch / ".mra-flow").mkdir(exist_ok=True)
        (self.orch / ".mra-flow/version").write_text(version + "\n")

    def tag(self, *names):
        for name in names:
            git(self.remote, "tag", name)

    def run_hook(self, remote=None):
        env = dict(self.env, CLAUDE_PROJECT_DIR=str(self.orch),
                   MRA_FLOW_REMOTE=str(remote or self.remote))
        done = subprocess.run([sys.executable, str(HOOK)], cwd=self.orch, env=env,
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        return done

    def run_cli(self, *args, remote=None):
        env = dict(self.env, CLAUDE_PROJECT_DIR=str(self.orch),
                   MRA_FLOW_REMOTE=str(remote or self.remote))
        return subprocess.run([sys.executable, str(HOOK), *args], cwd=self.orch, env=env,
                              capture_output=True, text=True)

    def state_path(self):
        return self.orch / ".mra-flow/update-state.json"

    def test_newer_tag_asks_now_later_or_ignore(self):
        self.tag("v0.1.19", "v0.1.21", "v0.2.0")
        payload = json.loads(self.run_hook().stdout)
        self.assertEqual(payload["systemMessage"],
                         "mra-flow 0.2.0 is available (installed: 0.1.20) — update now, later or ignore?")
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertIn("AskUserQuestion", context)
        self.assertIn("`.claude/skills/mra-flow-update/SKILL.md`", context)
        self.assertIn("python3 .mra-flow/hooks/check-update.py ignore 0.2.0", context)
        self.assertIn("Never update without the user's answer", context)

    def test_numeric_not_lexical_comparison(self):
        self.tag("v0.1.9", "v0.1.100")
        self.set_installed("0.1.20")
        self.assertIn("0.1.100 is available", self.run_hook().stdout)

    def test_equal_or_older_is_silent(self):
        self.tag("v0.1.19", "v0.1.20")
        self.assertEqual(self.run_hook().stdout, "")

    def test_non_semver_tags_ignored(self):
        self.tag("v9.0", "v1.2.3-rc1", "v1.2.3.4", "vfoo", "v0.1.20")
        self.assertEqual(self.run_hook().stdout, "")

    def test_throttle_reuses_state_without_remote(self):
        self.tag("v0.2.0")
        self.run_hook()
        shutil.rmtree(self.remote)
        again = self.run_hook()
        self.assertIn("0.2.0 is available", again.stdout)

    def test_rechecks_after_window(self):
        self.tag("v0.2.0")
        self.run_hook()
        state = json.loads(self.state_path().read_text())
        state["checked_at"] = time.time() - 25 * 3600
        self.state_path().write_text(json.dumps(state))
        self.tag("v0.3.0")
        self.assertIn("0.3.0 is available", self.run_hook().stdout)

    def test_window_is_four_hours(self):
        self.tag("v0.2.0")
        self.run_hook()
        self.tag("v0.3.0")
        state = json.loads(self.state_path().read_text())
        state["checked_at"] = time.time() - 3 * 3600
        self.state_path().write_text(json.dumps(state))
        self.assertIn("0.2.0 is available", self.run_hook().stdout)
        state["checked_at"] = time.time() - 5 * 3600
        self.state_path().write_text(json.dumps(state))
        self.assertIn("0.3.0 is available", self.run_hook().stdout)

    def test_repeats_every_session_until_answered(self):
        self.tag("v0.2.0")
        self.run_hook()
        self.assertIn("0.2.0 is available", self.run_hook().stdout)

    def test_ignore_silences_that_release_until_a_newer_one(self):
        self.tag("v0.2.0")
        self.run_hook()
        done = self.run_cli("ignore", "0.2.0")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.run_hook().stdout, "")
        self.tag("v0.2.1")
        self.assertIn("latest: 0.2.1\nstatus: update available\n", self.run_cli("check").stdout)
        self.assertIn("0.2.1 is available", self.run_hook().stdout)

    def test_ignore_rejects_a_non_release(self):
        self.assertEqual(self.run_cli("ignore", "latest").returncode, 1)

    def test_check_asks_the_remote_despite_the_window(self):
        self.tag("v0.2.0")
        self.run_hook()
        self.tag("v0.3.0")
        done = self.run_cli("check")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("installed: 0.1.20\nlatest: 0.3.0\nstatus: update available\n", done.stdout)
        self.assertEqual(json.loads(self.state_path().read_text())["latest"], "0.3.0")

    def test_check_reports_up_to_date_and_ignored(self):
        self.tag("v0.1.20")
        self.assertIn("status: up to date", self.run_cli("check").stdout)
        self.tag("v0.2.0")
        self.run_cli("ignore", "0.2.0")
        self.assertIn("status: update available (ignored)", self.run_cli("check").stdout)

    def test_check_with_unreachable_remote_exits_2(self):
        done = self.run_cli("check", remote=self.tmp / "missing.git")
        self.assertEqual(done.returncode, 2)
        self.assertIn("remote: unreachable", done.stdout)

    def test_cli_outside_an_orchestrator_fails(self):
        (self.orch / "mra-flow.toml").unlink()
        self.assertEqual(self.run_cli("check").returncode, 1)

    def test_unreachable_remote_is_silent(self):
        done = self.run_hook(remote=self.tmp / "missing.git")
        self.assertEqual(done.stdout, "")

    def test_bad_state_file_is_tolerated(self):
        self.tag("v0.2.0")
        self.state_path().write_text("{not json")
        self.assertIn("0.2.0 is available", self.run_hook().stdout)

    def test_not_an_orchestrator_is_silent(self):
        self.tag("v0.2.0")
        (self.orch / "mra-flow.toml").unlink()
        self.assertEqual(self.run_hook().stdout, "")

    def test_no_version_file_is_silent(self):
        self.tag("v0.2.0")
        (self.orch / ".mra-flow/version").unlink()
        self.assertEqual(self.run_hook().stdout, "")
