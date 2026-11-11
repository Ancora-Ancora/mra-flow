import json
import os
from pathlib import Path

from installer import reconcile as rc
from installer import shared_files as sf
from tests.support import (TmpTestCase, fake_env, git, make_orchestrator, make_package,
                           run_install, snapshot)


class UserLayerTest(TmpTestCase):
    def setUp(self):
        super().setUp()
        self.pkg = make_package(self.tmp)
        self.env = fake_env(self.tmp)
        self.claude = Path(self.env["CLAUDE_CONFIG_DIR"])
        self.excludes = Path(self.env["XDG_CONFIG_HOME"]) / "git" / "ignore"

    def user(self):
        done = run_install(self.pkg, "--user", self.env)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        return done.stdout

    def test_fresh_user_install(self):
        self.user()
        hook = self.claude / sf.HOOK_SCRIPT
        self.assertTrue(os.access(hook, os.X_OK))
        self.assertTrue((self.claude / "mra-flow/CLAUDE.md").is_file())
        self.assertTrue((self.claude / "agents/Explore.md").is_file())
        self.assertEqual(rc.load_manifest(self.claude, rc.USER_STATE).version, "0.1.0")
        self.assertEqual((self.claude / "CLAUDE.md").read_text(), sf.USER_IMPORT_LINE + "\n")
        settings = json.loads((self.claude / "settings.json").read_text())
        self.assertEqual(settings, {"hooks": {"SessionStart": [sf.hook_entry(self.claude)]}})
        self.assertIn("handoff/", self.excludes.read_text().splitlines())

    def test_user_reinstall_is_noop(self):
        self.user()
        before = snapshot(Path(self.env["HOME"]))
        self.user()
        self.assertEqual(snapshot(Path(self.env["HOME"])), before)

    def test_respects_core_excludes_file(self):
        custom = Path(self.env["HOME"]) / "my-ignore"
        custom.write_text("*.swp\n")
        Path(self.env["GIT_CONFIG_GLOBAL"]).write_text(f"[core]\n\texcludesFile = {custom}\n")
        self.user()
        self.assertEqual(custom.read_text().splitlines(), ["*.swp", "", "# mra-flow", "handoff/"])
        self.assertFalse(self.excludes.exists())

    def test_keeps_existing_user_claude_md_and_settings(self):
        self.claude.mkdir(parents=True)
        (self.claude / "CLAUDE.md").write_text("# Me\nBe terse.\n")
        (self.claude / "settings.json").write_text('{"model": "opus"}')
        self.user()
        self.assertTrue((self.claude / "CLAUDE.md").read_text().startswith("# Me\nBe terse.\n"))
        self.assertEqual(json.loads((self.claude / "settings.json").read_text())["model"], "opus")

    def test_adopts_identical_explore_agent(self):
        agent = self.claude / "agents/Explore.md"
        agent.parent.mkdir(parents=True)
        agent.write_bytes((self.pkg / "payload/user/agents/Explore.md").read_bytes())
        (self.claude / "agents/Mine.md").write_text("my own agent\n")
        self.user()
        self.assertIn("agents/Explore.md", rc.load_manifest(self.claude, rc.USER_STATE).files)
        self.assertEqual((self.claude / "agents/Mine.md").read_text(), "my own agent\n")

    def test_user_conflict_refuses(self):
        (self.claude / "mra-flow").mkdir(parents=True)
        (self.claude / "mra-flow/CLAUDE.md").write_text("hand-written\n")
        done = run_install(self.pkg, "--user", self.env)
        self.assertEqual(done.returncode, 1)
        self.assertIn("mra-flow/CLAUDE.md", done.stdout)
        self.assertFalse((self.claude / "settings.json").exists())

    def test_orchestrator_warns_until_user_layer_installed(self):
        orch = make_orchestrator(self.tmp)
        out = run_install(self.pkg, orch, self.env).stdout
        self.assertIn("run install.sh --user", out)
        self.user()
        out = run_install(self.pkg, orch, self.env).stdout
        self.assertNotIn("run install.sh --user", out)
        self.assertEqual(git(orch, "config", "beads.role"), "maintainer")
